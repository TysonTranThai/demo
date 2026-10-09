#!/usr/bin/env python3
"""
content_api.py — API nhỏ để giáo viên "Xuất bản" nội dung cho học sinh.

Chỉ dùng thư viện chuẩn của Python (máy chủ này không có PHP). Dịch vụ chỉ lắng
nghe trên 127.0.0.1 và được nginx chuyển tiếp tại /api/.

  GET  /api/health            → trạng thái
  GET  /api/session           → đã đăng nhập chưa (và hạn của phiên)
  POST /api/login             → đổi mật khẩu giáo viên lấy cookie đăng nhập
  POST /api/logout            → xoá phiên trên máy này
  GET  /api/content           → bản đã xuất bản (giống content/published.json)
  POST /api/content           → ghi một trang vào bản đã xuất bản (cần Bearer token)
  GET  /api/content/history   → danh sách bản lưu cũ
  POST /api/content/restore   → quay lại một bản lưu cũ (cần Bearer token)

Thiết kế an toàn:
  * Chỉ ghi được vào đúng thư mục dữ liệu; tên trang bị giới hạn ký tự, nên
    không thể trỏ tới đường dẫn khác.
  * Mọi bản ghi đều được kiểm tra kiểu dữ liệu và độ dài trước khi lưu.
  * Ghi theo kiểu "tệp tạm rồi đổi tên" (os.replace) nên học sinh đang tải trang
    không bao giờ đọc phải tệp dở dang.
  * Mỗi lần ghi đều lưu lại một bản cũ để giáo viên còn quay lại được.
  * So sánh mã bằng hmac.compare_digest (không lộ độ dài theo thời gian).
"""
import hmac
import json
import os
import re
import secrets
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

DATA_DIR = os.environ.get("SAH_DATA_DIR", "/var/www/smart-art-heritage/content")
HOST = os.environ.get("SAH_HOST", "127.0.0.1")
PORT = int(os.environ.get("SAH_PORT", "8788"))
TOKEN_FILE = os.environ.get("SAH_TOKEN_FILE", "/etc/sah-content-api/token")
PASSWORD_FILE = os.environ.get("SAH_PASSWORD_FILE", "/etc/sah-content-api/password")
# Phiên đăng nhập KHÔNG được nằm trong thư mục web phục vụ: đây là chứng chỉ
# đăng nhập của giáo viên. Mặc định /var/lib (không ai tải được qua HTTP);
# nếu thư mục đó không ghi được thì lùi về bộ nhớ (mất khi khởi động lại).
STATE_DIR = os.environ.get("SAH_STATE_DIR", "/var/lib/sah-content-api")
ORIGINS = [o.strip() for o in os.environ.get("SAH_ORIGINS", "").split(",") if o.strip()]

PUBLISHED = os.path.join(DATA_DIR, "published.json")
HISTORY_DIR = os.path.join(DATA_DIR, "history")
LOCK = os.path.join(DATA_DIR, ".publish.lock")

MAX_BODY = 4 * 1024 * 1024          # 4 MB
MAX_ENTRIES = 8000                  # số ô nội dung tối đa cho một trang
MAX_TEXT = 4000                     # độ dài một ô
MAX_PATH = 400
MAX_HISTORY = 60                    # số bản lưu giữ lại
MAX_SESSIONS = 400                  # số phiên đăng nhập giữ lại
SESSION_SECONDS = 90 * 24 * 3600    # "nhớ máy này" 90 ngày
COOKIE = "sah_session"
LOGIN_MAX_TRIES = 12                # số lần nhập sai cho phép trong cửa sổ dưới
LOGIN_WINDOW = 300
PAGE_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
PATH_RE = re.compile(r"^[A-Za-z0-9:()>_-]{1,%d}$" % MAX_PATH)


def token():
    t = os.environ.get("SAH_TOKEN")
    if t:
        return t.strip()
    try:
        with open(TOKEN_FILE, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def password():
    """Mật khẩu chung của tổ giáo viên (khác mã xuất bản dùng cho script)."""
    p = os.environ.get("SAH_PASSWORD")
    if p:
        return p.strip()
    try:
        with open(PASSWORD_FILE, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


# ------------------------------------------------------------------ phiên đăng nhập
# Giáo viên đăng nhập một lần, máy chủ trả về cookie HttpOnly; trình duyệt giữ
# cookie đó nên không ai phải dán mã xuất bản nữa. Mã vẫn dùng được cho script.
_SESSIONS = None                     # None = chưa nạp từ đĩa
_SESSIONS_MEM_ONLY = False
_LOGIN_FAILS = {}                    # ip -> [thời điểm, ...]


def _sessions_path():
    return os.path.join(STATE_DIR, "sessions.json")


def _load_sessions():
    global _SESSIONS
    if _SESSIONS is not None:
        return _SESSIONS
    _SESSIONS = {}
    try:
        with open(_sessions_path(), encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            _SESSIONS = {k: v for k, v in data.items() if isinstance(v, dict)}
    except (OSError, ValueError):
        pass
    return _SESSIONS


def _save_sessions():
    """Ghi ra đĩa nếu được; không ghi được thì vẫn chạy tiếp trong bộ nhớ."""
    global _SESSIONS_MEM_ONLY
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        tmp = _sessions_path() + ".tmp-%s" % secrets.token_hex(4)
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(_SESSIONS, fh, ensure_ascii=False, sort_keys=True)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, _sessions_path())
        _SESSIONS_MEM_ONLY = False
    except OSError as err:
        if not _SESSIONS_MEM_ONLY:
            _SESSIONS_MEM_ONLY = True
            sys.stderr.write(
                "CẢNH BÁO: không ghi được %s (%s) — phiên đăng nhập sẽ mất khi "
                "khởi động lại dịch vụ.\n" % (STATE_DIR, err))


def _prune_sessions(sessions):
    now = time.time()
    dead = [k for k, v in sessions.items() if not isinstance(v.get("exp"), (int, float)) or v["exp"] < now]
    for k in dead:
        sessions.pop(k, None)
    if len(sessions) > MAX_SESSIONS:
        for k, _ in sorted(sessions.items(), key=lambda kv: kv[1].get("exp", 0))[:len(sessions) - MAX_SESSIONS]:
            sessions.pop(k, None)
    return sessions


def new_session(ip):
    sessions = _prune_sessions(_load_sessions())
    sid = secrets.token_urlsafe(32)
    sessions[sid] = {"exp": time.time() + SESSION_SECONDS, "ip": ip[:64],
                     "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    _save_sessions()
    return sid


def session_ok(sid):
    if not sid:
        return False
    sessions = _load_sessions()
    rec = sessions.get(sid)
    if not isinstance(rec, dict):
        return False
    exp = rec.get("exp")
    if not isinstance(exp, (int, float)) or exp < time.time():
        sessions.pop(sid, None)
        _save_sessions()
        return False
    return True


def drop_session(sid):
    sessions = _load_sessions()
    if sid in sessions:
        sessions.pop(sid, None)
        _save_sessions()


def empty_store():
    return {"v": 1, "at": None, "by": "", "pages": {}}


def read_store():
    try:
        with open(PUBLISHED, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and isinstance(data.get("pages"), dict):
            return data
    except (OSError, ValueError):
        pass
    return empty_store()


def write_store(store, revision=True):
    """Ghi tệp tạm rồi đổi tên — người đọc luôn thấy một tệp hoàn chỉnh."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if revision and os.path.exists(PUBLISHED):
        os.makedirs(HISTORY_DIR, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dst = os.path.join(HISTORY_DIR, "%s-%s.json" % (stamp, secrets.token_hex(3)))
        try:
            with open(PUBLISHED, "rb") as src, open(dst, "wb") as out:
                out.write(src.read())
            prune_history()
        except OSError:
            pass
    tmp = PUBLISHED + ".tmp-%s" % secrets.token_hex(4)
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(store, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, PUBLISHED)


def prune_history():
    try:
        files = sorted(f for f in os.listdir(HISTORY_DIR) if f.endswith(".json"))
    except OSError:
        return
    for name in files[:-MAX_HISTORY]:
        try:
            os.remove(os.path.join(HISTORY_DIR, name))
        except OSError:
            pass


class Bad(Exception):
    pass


def clean_text_entry(key, entry):
    if not isinstance(entry, dict):
        raise Bad("mục nội dung không phải đối tượng")
    v = entry.get("v")
    if not isinstance(v, str) or not v.strip():
        raise Bad("thiếu nội dung mới")
    if len(v) > MAX_TEXT:
        raise Bad("nội dung quá dài")
    p = entry.get("p", "")
    if not isinstance(p, str) or len(p) > MAX_TEXT:
        raise Bad("nội dung gốc không hợp lệ")
    path = entry.get("path")
    if not isinstance(path, str) or not PATH_RE.match(path):
        raise Bad("đường dẫn ô không hợp lệ")
    idx = entry.get("i", 0)
    if not isinstance(idx, int) or isinstance(idx, bool) or idx < 0 or idx > 5000:
        raise Bad("vị trí ô không hợp lệ")
    out = {"v": v, "p": p, "path": path, "i": idx}
    for name in ("sec", "grp", "at", "from"):
        val = entry.get(name)
        if val is None:
            continue
        if not isinstance(val, str) or len(val) > MAX_PATH:
            raise Bad("trường %s không hợp lệ" % name)
        out[name] = val
    return out


def sanitize_page(payload):
    if not isinstance(payload, dict):
        raise Bad("dữ liệu gửi lên không hợp lệ")
    page = payload.get("page")
    if not isinstance(page, str) or not PAGE_RE.match(page):
        raise Bad("tên trang không hợp lệ")
    text = payload.get("text", {})
    if not isinstance(text, dict):
        raise Bad("danh sách ô nội dung không hợp lệ")
    if len(text) > MAX_ENTRIES:
        raise Bad("quá nhiều ô nội dung")
    clean = {}
    for key, entry in text.items():
        if not isinstance(key, str) or len(key) > 600:
            raise Bad("khoá ô nội dung không hợp lệ")
        clean[key] = clean_text_entry(key, entry)
    hidden = payload.get("hidden", [])
    if not isinstance(hidden, list):
        raise Bad("danh sách khối ẩn không hợp lệ")
    hidden = [h for h in hidden if isinstance(h, str) and re.match(r"^[A-Za-z0-9_-]{1,64}$", h)]
    return page, {"text": clean, "hidden": sorted(set(hidden))}


class Handler(BaseHTTPRequestHandler):
    server_version = "SAHContent/1.0"
    protocol_version = "HTTP/1.1"

    # ------------------------------------------------------------------ tiện ích
    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def cors(self):
        origin = self.headers.get("Origin")
        if origin and origin in ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            # Cookie đăng nhập chỉ dùng được ở tên miền đã cho phép tường minh
            # (không được dùng "*" khi có credentials).
            self.send_header("Access-Control-Allow-Credentials", "true")

    def send_json(self, code, obj, cache=False, cookie=None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store" if not cache else "public, max-age=60")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.cors()
        self.end_headers()
        self.wfile.write(body)

    def cookie_header(self, value, max_age):
        """HttpOnly: JavaScript không đọc được phiên. Path=/api để cookie không
        bị gửi kèm mọi ảnh/trang tĩnh. SameSite=Lax chặn trình duyệt gửi cookie
        trong yêu cầu POST từ trang khác (chống CSRF)."""
        secure = ""
        if (self.headers.get("X-Forwarded-Proto") or "").lower() == "https":
            secure = "; Secure"
        return "%s=%s; Path=/api; Max-Age=%d; HttpOnly; SameSite=Lax%s" % (
            COOKIE, value, max_age, secure)

    def cookie_sid(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            name, _, value = part.strip().partition("=")
            if name == COOKIE:
                return value.strip()
        return ""

    def same_site(self):
        """Cookie do trình duyệt tự gửi kèm, nên thay đổi chỉ được nhận khi yêu
        cầu đến từ chính trang này (hoặc tên miền đã cho phép). Thiếu kiểm tra
        này thì một trang khác có thể lén đăng nội dung lên trang của trường."""
        origin = self.headers.get("Origin")
        host = self.headers.get("Host", "")
        if origin:
            if origin in ORIGINS:
                return True
            return origin in ("http://" + host, "https://" + host)
        site = self.headers.get("Sec-Fetch-Site")
        if site and site not in ("same-origin", "none"):
            return False
        return True                     # script/curl: không có Origin

    def authorized(self):
        """Cookie đăng nhập của giáo viên HOẶC mã xuất bản Bearer (script)."""
        if not token() and not password():
            self.send_json(503, {"error": "máy chủ chưa được đặt mật khẩu giáo viên"})
            return False
        want = token()
        got = self.headers.get("Authorization", "")
        if got.startswith("Bearer "):
            got = got[7:]
        got = got.strip()
        if want and got and hmac.compare_digest(got, want):
            return True
        if session_ok(self.cookie_sid()):
            if not self.same_site():
                self.send_json(403, {"error": "yêu cầu từ tên miền khác bị từ chối"})
                return False
            return True
        self.send_json(401, {"error": "chưa đăng nhập"})
        return False

    def read_body(self):
        """Đọc TRỌN phần thân yêu cầu trước khi trả lời bất cứ điều gì.

        Nếu từ chối (401/413) mà chưa đọc hết thân, phần còn lại của yêu cầu sẽ
        bị hiểu nhầm thành yêu cầu kế tiếp trên cùng kết nối keep-alive. Đó là
        lỗi đã gặp thật: log ghi "Bad request syntax" ngay sau một lần 401.
        """
        raw_len = self.headers.get("Content-Length")
        try:
            length = int(raw_len or 0)
        except ValueError:
            self.close_connection = True
            raise Bad("độ dài không hợp lệ")
        if length <= 0:
            self.close_connection = True
            raise Bad("thiếu dữ liệu")
        if length > MAX_BODY:
            self.close_connection = True
            raise Bad("dữ liệu quá lớn")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise Bad("dữ liệu không phải JSON hợp lệ")

    # -------------------------------------------------------------------- routes
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.cors()
        self.end_headers()

    # ------------------------------------------------------------- đăng nhập
    def login_allowed(self, ip):
        now = time.time()
        tries = [t for t in _LOGIN_FAILS.get(ip, []) if now - t < LOGIN_WINDOW]
        _LOGIN_FAILS[ip] = tries
        return len(tries) < LOGIN_MAX_TRIES

    def do_login(self, payload):
        want = password()
        if not want:
            return self.send_json(503, {"error": "máy chủ chưa được đặt mật khẩu giáo viên"})
        ip = self.address_string()
        if not self.login_allowed(ip):
            return self.send_json(429, {"error": "nhập sai quá nhiều lần, xin thử lại sau vài phút"})
        got = payload.get("password") if isinstance(payload, dict) else None
        if not isinstance(got, str) or not hmac.compare_digest(got.strip(), want):
            _LOGIN_FAILS.setdefault(ip, []).append(time.time())
            self.log_message("login FAILED from %s", ip)
            return self.send_json(401, {"error": "mật khẩu không đúng"})
        _LOGIN_FAILS.pop(ip, None)
        sid = new_session(ip)
        self.log_message("login ok from %s", ip)
        return self.send_json(
            200,
            {"ok": True,
             "until": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + SESSION_SECONDS))},
            cookie=self.cookie_header(sid, SESSION_SECONDS))

    def do_logout(self):
        drop_session(self.cookie_sid())
        return self.send_json(200, {"ok": True}, cookie=self.cookie_header("", 0))

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/api/health":
            return self.send_json(200, {"ok": True, "pages": sorted(read_store()["pages"]),
                                        "at": read_store().get("at"),
                                        "passwordSet": bool(password()),
                                        "tokenSet": bool(token())})
        if path == "/api/content":
            return self.send_json(200, read_store())
        if path == "/api/session":
            sid = self.cookie_sid()
            rec = _load_sessions().get(sid) if sid else None
            exp = rec.get("exp") if isinstance(rec, dict) else None
            if not session_ok(sid):
                exp = None
            return self.send_json(200, {
                "signedIn": exp is not None,
                "until": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(exp)) if exp else None,
                "hasPassword": bool(password()),
            })
        if path == "/api/content/history":
            items = []
            try:
                for name in sorted(os.listdir(HISTORY_DIR), reverse=True)[:40]:
                    if not name.endswith(".json"):
                        continue
                    full = os.path.join(HISTORY_DIR, name)
                    try:
                        with open(full, encoding="utf-8") as fh:
                            snap = json.load(fh)
                        items.append({"rev": name, "at": snap.get("at"),
                                      "pages": sorted((snap.get("pages") or {}).keys()),
                                      "size": os.path.getsize(full)})
                    except (OSError, ValueError):
                        continue
            except OSError:
                pass
            return self.send_json(200, {"revisions": items})
        self.send_json(404, {"error": "không có đường dẫn này"})

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path not in ("/api/content", "/api/content/restore", "/api/login", "/api/logout"):
            self.close_connection = True
            return self.send_json(404, {"error": "không có đường dẫn này"})
        # Đọc thân yêu cầu TRƯỚC khi xét mã, để kết nối không bị lệch.
        try:
            payload = self.read_body()
        except Bad as err:
            return self.send_json(400, {"error": str(err)})
        if path == "/api/login":
            return self.do_login(payload)
        if path == "/api/logout":
            return self.do_logout()
        if not self.authorized():
            return

        if path == "/api/content":
            try:
                page, clean = sanitize_page(payload)
            except Bad as err:
                return self.send_json(400, {"error": str(err)})
            store = read_store()
            store["v"] = 1
            store["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            store["by"] = "teacher"
            store["pages"][page] = clean
            try:
                write_store(store)
            except OSError as err:
                return self.send_json(500, {"error": "không ghi được tệp: %s" % err})
            self.log_message("published page=%s entries=%d hidden=%d",
                             page, len(clean["text"]), len(clean["hidden"]))
            return self.send_json(200, {"ok": True, "at": store["at"], "page": page,
                                        "entries": len(clean["text"])})

        # restore
        rev = payload.get("rev") if isinstance(payload, dict) else None
        if not isinstance(rev, str) or not re.match(r"^[A-Za-z0-9._-]{1,80}\.json$", rev):
            return self.send_json(400, {"error": "tên bản lưu không hợp lệ"})
        full = os.path.join(HISTORY_DIR, rev)
        if not os.path.isfile(full):
            return self.send_json(404, {"error": "không tìm thấy bản lưu"})
        try:
            with open(full, encoding="utf-8") as fh:
                snap = json.load(fh)
        except (OSError, ValueError):
            return self.send_json(500, {"error": "bản lưu bị hỏng"})
        if not isinstance(snap, dict) or not isinstance(snap.get("pages"), dict):
            return self.send_json(500, {"error": "bản lưu không hợp lệ"})
        snap["at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        try:
            write_store(snap)
        except OSError as err:
            return self.send_json(500, {"error": "không ghi được tệp: %s" % err})
        self.log_message("restored rev=%s", rev)
        return self.send_json(200, {"ok": True, "at": snap["at"]})


def main():
    if not token() and not password():
        sys.stderr.write(
            "CẢNH BÁO: chưa có mật khẩu giáo viên lẫn mã xuất bản\n"
            "  (SAH_PASSWORD / %s, SAH_TOKEN / %s).\n"
            "Mọi yêu cầu ghi sẽ bị từ chối cho tới khi đặt một trong hai.\n"
            % (PASSWORD_FILE, TOKEN_FILE))
    elif not password():
        sys.stderr.write(
            "LƯU Ý: chưa có mật khẩu giáo viên (%s) — giáo viên chưa đăng nhập\n"
            "  được trong trình duyệt, chỉ còn đường dùng mã xuất bản.\n" % PASSWORD_FILE)
    _load_sessions()
    os.makedirs(DATA_DIR, exist_ok=True)
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    srv.daemon_threads = True
    print("sah-content-api nghe tại %s:%d, dữ liệu ở %s" % (HOST, PORT, DATA_DIR), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()

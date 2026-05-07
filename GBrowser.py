# GBROWSER 2025 — Full-featured Python browser (ported from Ceprkac C#)
# Python 3.13 + PyQt6 + PyQt6-WebEngine compatible
# Logic-matched to Ceprkac: OAuth popups, downloads, custom tab strip, auth callbacks
import sys
import os
import json
import csv
import re
import hashlib
import html as html_module
import time
from urllib.parse import urlparse, quote_plus
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import *
from PyQt6.QtCore import Qt, QUrl, QTimer, QByteArray, QPoint, QRect, QSize, pyqtSignal
from PyQt6.QtGui import (QIcon, QPainter, QPixmap, QColor, QFont, QPen, QBrush,
                          QKeySequence, QShortcut, QPainterPath, QAction, QFontMetrics)

# === Fernet fallback for non-Windows password encryption ===
try:
    from cryptography.fernet import Fernet as _Fernet
    import base64 as _base64
    _HAS_FERNET = True
except ImportError:
    _HAS_FERNET = False

# === CONFIG ===
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".gorstak_browser")
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(os.path.join(CONFIG_DIR, "storage"), exist_ok=True)
os.makedirs(os.path.join(CONFIG_DIR, "cache"), exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
BOOKMARKS_FILE = os.path.join(CONFIG_DIR, "bookmarks.txt")
HISTORY_FILE = os.path.join(CONFIG_DIR, "history.txt")
PASSWORDS_FILE = os.path.join(CONFIG_DIR, "passwords.dat")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.txt")

# === COLOUR PALETTE (Chrome-dark inspired, matching Ceprkac) ===
class Theme:
    TitleBar    = QColor(32, 33, 36)
    TabBar      = QColor(32, 33, 36)
    ActiveTab   = QColor(53, 54, 58)
    InactiveTab = QColor(40, 41, 45)
    TabHover    = QColor(48, 49, 53)
    Toolbar     = QColor(53, 54, 58)
    AddressBox  = QColor(41, 42, 45)
    BookmarkBar = QColor(53, 54, 58)
    StatusBar   = QColor(32, 33, 36)
    ForeLight   = QColor(255, 255, 255)
    ForeDim     = QColor(180, 184, 190)
    Accent      = QColor(138, 180, 248)
    CloseHover  = QColor(200, 60, 60)
    Border      = QColor(60, 64, 67)


# === DPAPI (Windows credential encryption) ===
try:
    import win32crypt
    from ctypes import windll
    DPAPI = True
except ImportError:
    DPAPI = False


if _HAS_FERNET:
    def _get_fernet_key() -> bytes:
        """Derive a Fernet key from machine hostname + username for non-DPAPI fallback."""
        import socket, getpass
        seed = f"{socket.gethostname()}|{getpass.getuser()}".encode("utf-8")
        key_bytes = hashlib.sha256(seed).digest()
        return _base64.urlsafe_b64encode(key_bytes)


# === SEARCH ENGINES ===
SEARCH_ENGINES = [
    ("Google",       "https://www.google.com",    "https://www.google.com/search?q={}"),
    ("Bing",         "https://www.bing.com",      "https://www.bing.com/search?q={}"),
    ("DuckDuckGo",   "https://duckduckgo.com",    "https://duckduckgo.com/?q={}"),
    ("Yahoo",        "https://search.yahoo.com",  "https://search.yahoo.com/search?p={}"),
    ("Brave Search", "https://search.brave.com",  "https://search.brave.com/search?q={}"),
    ("Startpage",    "https://www.startpage.com", "https://www.startpage.com/do/search?q={}"),
]

# === AD BLOCKER DOMAIN LISTS (Same as Ceprkac) ===
BLOCKED_AD_DOMAINS: set[str] = {
    # Google Ads & Analytics
    "doubleclick.net","googleadservices.com","googlesyndication.com","adservice.google.com",
    "ads.google.com","google-analytics.com","googletagmanager.com","googletagservices.com",
    "pagead2.googlesyndication.com","pagead2.googleadservices.com",
    # Major ad networks
    "adnxs.com","taboola.com","outbrain.com","criteo.com","scorecardresearch.com","pubmatic.com",
    "rubiconproject.com","quantserve.com","quantcast.com","omniture.com","comscore.com",
    "krux.com","bluekai.com","exelate.com","adform.com","adroll.com","vungle.com","inmobi.com",
    "flurry.com","mixpanel.com","heap.io","amplitude.com","optimizely.com","bizible.com",
    "pardot.com","hubspot.com","marketo.com","eloqua.com","media.net","appnexus.com","adbrite.com",
    "admob.com","adsonar.com","zergnet.com","revcontent.com","mgid.com","adblade.com","adcolony.com",
    "chartbeat.com","newrelic.com","pingdom.net","kissmetrics.com","tradedesk.com","turn.com",
    "adscale.com","bannerflow.com","nativeads.com","contentad.com","displayads.com",
    "smartadserver.com","openx.net","casalemedia.com","indexww.com","sharethrough.com",
    "33across.com","triplelift.com","sovrn.com","lijit.com","bidswitch.net","yieldmo.com",
    "teads.tv","spotxchange.com","springserve.com","contextweb.com","liveintent.com",
    "adtech.de","adform.net","serving-sys.com","adsafeprotected.com","moatads.com",
    # Facebook / Meta
    "connect.facebook.net","pixel.facebook.com","analytics.facebook.com","ads.facebook.com","an.facebook.com",
    # Twitter / X
    "ads-twitter.com","static.ads-twitter.com","analytics.twitter.com","ads-api.twitter.com","advertising.twitter.com",
    # Reddit
    "pixel.reddit.com","rereddit.com","ads.reddit.com","events.reddit.com","events.redditmedia.com","d.reddit.com",
    # LinkedIn
    "ads.linkedin.com","analytics.pointdrive.linkedin.com",
    # TikTok
    "analytics.tiktok.com","ads.tiktok.com","ads-sg.tiktok.com","analytics-sg.tiktok.com",
    # Pinterest
    "ads.pinterest.com","log.pinterest.com","ads-dev.pinterest.com","analytics.pinterest.com",
    "trk.pinterest.com","trk2.pinterest.com","widgets.pinterest.com",
    # Amazon
    "amazon-adsystem.com","advertising-api-eu.amazon.com","amazonaax.com","amazonclix.com","assoc-amazon.com",
    # YouTube
    "youtubeads.googleapis.com","ads.youtube.com","analytics.youtube.com","video-stats.video.google.com",
    "youtube.cleverads.vn",
    # Yahoo
    "advertising.yahoo.com","ads.yahoo.com","adserver.yahoo.com","global.adserver.yahoo.com",
    "adspecs.yahoo.com","analytics.yahoo.com","analytics.query.yahoo.com","comet.yahoo.com",
    "log.fc.yahoo.com","ganon.yahoo.com","gemini.yahoo.com","beap.gemini.yahoo.com",
    "geo.yahoo.com","marketingsolutions.yahoo.com","pclick.yahoo.com",
    "ads.yap.yahoo.com","m.yap.yahoo.com","partnerads.ysm.yahoo.com",
    # Yandex
    "appmetrica.yandex.com","yandexadexchange.net","adfox.yandex.ru","adsdk.yandex.ru",
    "an.yandex.ru","awaps.yandex.ru","awsync.yandex.ru","bs.yandex.ru","bs-meta.yandex.ru",
    "clck.yandex.ru","informer.yandex.ru","kiks.yandex.ru","mc.yandex.ru","metrika.yandex.ru",
    "share.yandex.ru","offerwall.yandex.net",
    # Hotjar / Session recording
    "hotjar.com","api-hotjar.com","hotjar-analytics.com","fullstory.com","mouseflow.com",
    "luckyorange.com","luckyorange.net","freshmarketer.com",
    # Segment / Analytics
    "segment.io","segment.com","stats.wp.com",
    # Error trackers
    "notify.bugsnag.com","sessions.bugsnag.com","api.bugsnag.com","app.bugsnag.com",
    "browser.sentry-cdn.com","app.getsentry.com",
    # FastClick
    "fastclick.com","fastclick.net",
    # Samsung
    "samsungadhub.com","samsungads.com","smetrics.samsung.com","nmetrics.samsung.com",
    "analytics.samsungknox.com","bigdata.ssp.samsung.com","config.samsungads.com",
    # Apple metrics
    "metrics.apple.com","securemetrics.apple.com","supportmetrics.apple.com",
    "metrics.icloud.com","metrics.mzstatic.com","books-analytics-events.apple.com",
    "stocks-analytics-events.apple.com",
    # Xiaomi
    "api.ad.xiaomi.com","data.mistat.xiaomi.com","sdkconfig.ad.xiaomi.com",
    "globalapi.ad.xiaomi.com","tracking.miui.com","tracking.intl.miui.com",
    # Huawei
    "metrics.data.hicloud.com","logservice.hicloud.com","logbak.hicloud.com",
    # OPPO / Realme / OnePlus
    "adsfs.oppomobile.com","bdapi-in-ads.realmemobile.com",
    "analytics.oneplus.cn","click.oneplus.cn","click.oneplus.com","open.oneplus.net",
    # Additional
    "events.hotjar.io","extmaps-api.yandex.net","metrics2.data.hicloud.com",
    "logservice1.hicloud.com","iot-eu-logser.realme.com","click.googleanalytics.com",
    "grs.hicloud.com","udcm.yahoo.com","auction.unityads.unity3d.com",
    "config.unityads.unity3d.com","adserver.unityads.unity3d.com","webview.unityads.unity3d.com",
    "adfstat.yandex.ru","iadsdk.apple.com","appmetrica.yandex.ru",
    "business-api.tiktok.com","log.byteoversea.com","ads-api.tiktok.com",
    "iot-logser.realme.com","tracking.rus.miui.com","adtech.yahooinc.com",
    "bdapi-ads.realmemobile.com","ck.ads.oppomobile.com","data.ads.oppomobile.com",
    "adx.ads.oppomobile.com","data.mistat.india.xiaomi.com","data.mistat.rus.xiaomi.com",
    "notes-analytics-events.apple.com","weather-analytics-events.apple.com",
    "api-adservices.apple.com","samsung-com.112.2o7.net","analytics-api.samsunghealthcn.com",
    "unityads.unity3d.com","byteoversea.com","yahooinc.com",
    # S3-hosted ad/analytics buckets
    "adtago.s3.amazonaws.com","analyticsengine.s3.amazonaws.com",
    "analytics.s3.amazonaws.com","advice-ads.s3.amazonaws.com",
    # Adult site ad networks
    "trafficjunky.com","trafficjunky.net","trafficstars.com","tsyndicate.com",
    "exoclick.com","exosrv.com","exoticads.com","juicyads.com","realsrv.com",
    "adsrv.org","padsdel.com","syndication.exoclick.com",
    "main.exoclick.com","static.exoclick.com","ads.trafficjunky.net",
    "cdn.trafficjunky.net","a.realsrv.com",
    "syndication.realsrv.com","s.magsrv.com","magsrv.com",
    # Additional missing
    "sdkconfig.ad.intl.xiaomi.com",
    "2mdn.net","2o7.net","adnxs.net","adsrvr.org","demdex.net","doubleverify.com",
    "eyeota.net","mathtag.com","nexac.com","nr-data.net","onesignal.com",
    "pushwoosh.com","rfihub.com","rlcdn.com","rubiconproject.net","sascdn.com",
    "simpli.fi","sitescout.com","tapad.com","tealiumiq.com","tidaltv.com",
    "treasuredata.com","tynt.com","undertone.com","visualwebsiteoptimizer.com",
    "w55c.net","weborama.com","webtrends.com","zqtk.net","crazyegg.com",
    "inspectlet.com","loggly.com",
}

AD_BLOCK_WHITELIST: set[str] = {
    "discord.com","discordapp.com","discord.gg","discord.media",
    "apple.com","icloud.com","ebay.com","paypal.com","mediafire.com",
    # Auth/OAuth providers
    "accounts.google.com","accounts.youtube.com","myaccount.google.com",
    "google.com","www.google.com","google.hr","google.co.uk",
    "youtube.com","www.youtube.com",
    "login.microsoftonline.com","login.live.com","login.microsoft.com",
    "appleid.apple.com","idmsa.apple.com",
    "github.com","auth0.com","okta.com",
    "apis.google.com","ssl.gstatic.com",
    "pay.google.com","payments.google.com",
    "gog.com","auth.gog.com","login.gog.com",
    "suno.com","suno.ai","clerk.suno.com",
    # AI services
    "openai.com","chat.openai.com","chatgpt.com",
    "claude.ai","anthropic.com",
    "gemini.google.com","bard.google.com",
    "perplexity.ai","you.com",
    "midjourney.com","stability.ai",
    "huggingface.co","replicate.com",
    "udio.com","poe.com","character.ai",
    "copilot.microsoft.com",
    # Banking & financial
    "chase.com","bankofamerica.com","wellsfargo.com","citibank.com",
    "usbank.com","capitalone.com","discover.com","americanexpress.com",
    "hsbc.com","barclays.com","natwest.com","lloydsbank.com",
    "revolut.com","wise.com","transferwise.com","stripe.com",
    "squareup.com","venmo.com","zelle.com","cash.app",
    "ing.com","raiffeisen.hr","pbz.hr","zaba.hr","erstebank.hr",
    "n26.com","monzo.com","starlingbank.com",
    # Gaming clients & stores
    "steampowered.com","store.steampowered.com","steamcommunity.com",
    "epicgames.com","unrealengine.com",
    "gogalaxy.com","ea.com","origin.com",
    "ubisoft.com","ubi.com",
    "blizzard.com","battle.net","battlenet.com.cn",
    "riotgames.com","leagueoflegends.com",
    "xbox.com","xboxlive.com",
    "playstation.com","sonyentertainmentnetwork.com",
    "nintendo.com","nintendo.net",
    "humblebundle.com","itch.io","indiegala.com",
    "twitch.tv",
}


# === OAuth/AUTH DOMAINS (Same as Ceprkac) ===
AUTH_DOMAINS = [
    "accounts.google.com", "/gsi/", "appleid.apple.com", "login.microsoftonline.com",
    "api.twitter.com", "twitter.com/i/oauth", "x.com/i/oauth", "/oauth", "/auth/",
    "/authorize", "/signin", "/sso", "pay.google.com", "payments.google.com",
    "clerk.", "suno.com", "suno.ai"
]

def _is_auth_url(url: str) -> bool:
    """Check if URL is an auth/OAuth flow that should open in popup."""
    url_lower = url.lower()
    return any(auth in url_lower for auth in AUTH_DOMAINS)


def _is_whitelisted(host: str) -> bool:
    """Check if host or any parent domain is whitelisted."""
    h = host.lower()
    while "." in h:
        if h in AD_BLOCK_WHITELIST:
            return True
        h = h[h.index(".") + 1:]
    return False


def _is_ad_domain(host: str) -> bool:
    """Check if host or any parent domain is in the blocked set."""
    h = host.lower()
    while "." in h:
        if h in BLOCKED_AD_DOMAINS:
            return True
        h = h[h.index(".") + 1:]
    return False


def _is_ad_url(url: str) -> bool:
    """Check if a URL points to a known ad/tracking domain."""
    try:
        parsed = urlparse(url if "://" in url else "https://" + url)
        host = parsed.hostname or ""
        host = host.lower()
        if _is_whitelisted(host):
            return False
        if _is_ad_domain(host):
            return True
        if any(p in url for p in ["/pagead/", "/adclick", "/aclk?",
               "googleadservices.com", "doubleclick.net", "googlesyndication.com"]):
            return True
    except Exception:
        pass
    return False


def _load_blocklist_file(path: str):
    """Load domains from a blocklist file into BLOCKED_AD_DOMAINS."""
    if not os.path.exists(path):
        return 0
    count = 0
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            domain = line.strip()
            if domain and not domain.startswith("#") and "." in domain:
                BLOCKED_AD_DOMAINS.add(domain)
                count += 1
    return count


# === PASSWORD MANAGER (Same logic as Ceprkac, with Fernet fallback) ===
class SavedCredential:
    def __init__(self, url="", username="", password=""):
        self.url = url
        self.username = username
        self.password = password


class PasswordManager:
    def __init__(self):
        self.passwords: list[SavedCredential] = []
        self.load()

    def load(self):
        if not os.path.exists(PASSWORDS_FILE):
            return
        try:
            with open(PASSWORDS_FILE, "rb") as f:
                encrypted = f.read()
            if DPAPI:
                import win32crypt
                decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
            elif _HAS_FERNET:
                fernet = _Fernet(_get_fernet_key())
                decrypted = fernet.decrypt(encrypted)
            else:
                decrypted = encrypted
            data = json.loads(decrypted.decode("utf-8"))
            self.passwords = [SavedCredential(e.get("u", ""), e.get("n", ""), e.get("p", "")) for e in data]
        except Exception:
            pass

    def save(self):
        try:
            data = [{"u": c.url, "n": c.username, "p": c.password} for c in self.passwords]
            raw = json.dumps(data).encode("utf-8")
            if DPAPI:
                import win32crypt
                encrypted = win32crypt.CryptProtectData(raw, None, None, None, None, 0)
            elif _HAS_FERNET:
                fernet = _Fernet(_get_fernet_key())
                encrypted = fernet.encrypt(raw)
            else:
                encrypted = raw
            with open(PASSWORDS_FILE, "wb") as f:
                f.write(encrypted)
        except Exception:
            pass

    def get_matches(self, domain: str) -> list[SavedCredential]:
        matches = []
        for p in self.passwords:
            try:
                if urlparse(p.url).hostname and urlparse(p.url).hostname.lower() == domain:
                    matches.append(p)
            except Exception:
                pass
        return matches

    def import_csv(self, filepath: str) -> int:
        """Import Chrome/Edge CSV format: name,url,username,password
        With sanitization: length limits and control character filtering."""
        _MAX_FIELD_LEN = 2048
        _CONTROL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
        count = 0
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            for row in reader:
                if len(row) < 4:
                    continue
                url, username, password = row[1].strip(), row[2].strip(), row[3].strip()
                # Length limits
                if len(url) > _MAX_FIELD_LEN or len(username) > _MAX_FIELD_LEN or len(password) > _MAX_FIELD_LEN:
                    continue
                # Skip rows with control characters
                if _CONTROL_RE.search(url) or _CONTROL_RE.search(username) or _CONTROL_RE.search(password):
                    continue
                if not url or not username:
                    continue
                if not any(p.url.lower() == url.lower() and p.username.lower() == username.lower()
                           for p in self.passwords):
                    self.passwords.append(SavedCredential(url, username, password))
                    count += 1
        self.save()
        return count

    def clear(self):
        self.passwords.clear()
        self.save()


# === BOOKMARK DATA MODEL (Same as Ceprkac) ===
class BookmarkNode:
    def __init__(self, type_="link", title="", href="", children=None):
        self.type = type_
        self.title = title
        self.href = href
        self.children: list[BookmarkNode] = children or []


def _load_bookmarks() -> list[BookmarkNode]:
    if not os.path.exists(BOOKMARKS_FILE):
        return []
    nodes: list[BookmarkNode] = []
    stack: list[list[BookmarkNode]] = [nodes]
    with open(BOOKMARKS_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if not line.strip():
                continue
            parts = line.split("\t", 2)
            if len(parts) < 2:
                parts = line.split("|", 2)
            current = stack[-1]
            if parts[0] == "FOLDER" and len(parts) >= 2:
                folder = BookmarkNode("folder", parts[1])
                current.append(folder)
                stack.append(folder.children)
            elif parts[0] == "ENDFOLDER":
                if len(stack) > 1:
                    stack.pop()
            elif parts[0] == "LINK" and len(parts) >= 3:
                current.append(BookmarkNode("link", parts[1], parts[2]))
            else:
                legacy = line.split("|", 1)
                if len(legacy) == 2:
                    current.append(BookmarkNode("link", legacy[0], legacy[1]))
                else:
                    current.append(BookmarkNode("link", _display_title(line), line))
    return nodes


def _save_bookmarks(nodes: list[BookmarkNode]):
    lines: list[str] = []
    _write_bookmark_nodes(lines, nodes)
    with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _write_bookmark_nodes(lines: list[str], nodes: list[BookmarkNode]):
    for node in nodes:
        if node.type == "folder":
            lines.append(f"FOLDER\t{node.title}")
            _write_bookmark_nodes(lines, node.children)
            lines.append("ENDFOLDER")
        else:
            lines.append(f"LINK\t{node.title}\t{node.href}")


def _bookmark_exists(nodes: list[BookmarkNode], url: str) -> bool:
    for n in nodes:
        if n.type == "link" and n.href.lower() == url.lower():
            return True
        if n.type == "folder" and _bookmark_exists(n.children, url):
            return True
    return False


def _remove_bookmark(nodes: list[BookmarkNode], url: str) -> bool:
    for i, n in enumerate(nodes):
        if n.type == "link" and n.href.lower() == url.lower():
            nodes.pop(i)
            return True
        if n.type == "folder" and _remove_bookmark(n.children, url):
            return True
    return False


def _count_links(nodes: list[BookmarkNode]) -> int:
    count = 0
    for n in nodes:
        if n.type == "link":
            count += 1
        elif n.type == "folder":
            count += _count_links(n.children)
    return count


def _display_title(url: str) -> str:
    try:
        return urlparse(url).hostname or url[:30]
    except Exception:
        return url[:30] if len(url) > 30 else url


def _collect_bookmark_urls(nodes: list[BookmarkNode]) -> list[str]:
    """Collect all bookmark URLs for autocomplete."""
    urls = []
    for n in nodes:
        if n.type == "link":
            urls.append(n.href)
        elif n.type == "folder":
            urls.extend(_collect_bookmark_urls(n.children))
    return urls


# === BOOKMARK HTML IMPORT/EXPORT (Same as Ceprkac) ===
def _parse_bookmarks_html(html_text: str) -> list[BookmarkNode]:
    """Parse Netscape bookmark HTML format with nested folders."""
    dl_start = html_text.lower().find("<dl")
    if dl_start >= 0:
        result, _ = _parse_dl(html_text, dl_start)
        while len(result) == 1 and result[0].type == "folder":
            result = result[0].children
        return result
    result = []
    for m in re.finditer(r'<a\s[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html_text, re.IGNORECASE | re.DOTALL):
        href, title = m.group(1), re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if href:
            result.append(BookmarkNode("link", title or _display_title(href), href))
    return result


def _parse_dl(html_text: str, pos: int) -> tuple[list[BookmarkNode], int]:
    nodes: list[BookmarkNode] = []
    tag_end = html_text.find(">", pos)
    if tag_end < 0:
        return nodes, pos
    pos = tag_end + 1
    length = len(html_text)

    while pos < length:
        next_tag = html_text.find("<", pos)
        if next_tag < 0:
            break
        pos = next_tag
        close_angle = html_text.find(">", pos)
        if close_angle < 0:
            break
        tag = html_text[pos:close_angle + 1]
        tag_upper = tag.upper()

        if tag_upper.startswith("</DL"):
            pos = close_angle + 1
            return nodes, pos

        if tag_upper.startswith("<DT") or tag_upper.startswith("<P") or tag_upper.startswith("<DD"):
            pos = close_angle + 1
            continue

        if tag_upper.startswith("<H3") or tag_upper.startswith("<H1") or tag_upper.startswith("<H2"):
            pos = close_angle + 1
            close_tag = "</" + tag[1:3] + ">"
            h_end = html_text.lower().find(close_tag.lower(), pos)
            folder_title = "Folder"
            if h_end > pos:
                folder_title = re.sub(r'<[^>]+>', '', html_text[pos:h_end]).strip()
                pos = h_end + len(close_tag)
            search_limit = min(pos + 200, length)
            child_dl = html_text.lower().find("<dl", pos, search_limit)
            children = []
            if child_dl >= 0:
                children, pos = _parse_dl(html_text, child_dl)
            nodes.append(BookmarkNode("folder", folder_title, children=children))
            continue

        if tag_upper.startswith("<A ") and "HREF" in tag_upper:
            href_match = re.search(r'href="([^"]*)"', tag, re.IGNORECASE)
            href = href_match.group(1) if href_match else ""
            pos = close_angle + 1
            a_end = html_text.lower().find("</a>", pos)
            title = ""
            if a_end > pos:
                title = re.sub(r'<[^>]+>', '', html_text[pos:a_end]).strip()
                pos = a_end + 4
            if href:
                nodes.append(BookmarkNode("link", title or _display_title(href), href))
            continue

        pos = close_angle + 1

    return nodes, pos


def _export_bookmarks_html(nodes: list[BookmarkNode], filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n')
        f.write('<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n')
        f.write('<TITLE>Bookmarks</TITLE>\n')
        f.write('<H1>Bookmarks</H1>\n')
        f.write('<DL><p>\n')
        _write_bookmarks_html(f, nodes, "    ")
        f.write('</DL><p>\n')


def _write_bookmarks_html(f, nodes: list[BookmarkNode], indent: str):
    for node in nodes:
        if node.type == "folder":
            safe_title = html_module.escape(node.title)
            f.write(f'{indent}<DT><H3>{safe_title}</H3>\n')
            f.write(f'{indent}<DL><p>\n')
            _write_bookmarks_html(f, node.children, indent + "    ")
            f.write(f'{indent}</DL><p>\n')
        else:
            safe_title = html_module.escape(node.title)
            safe_url = html_module.escape(node.href)
            f.write(f'{indent}<DT><A HREF="{safe_url}">{safe_title}</A>\n')


# === SETTINGS (Same as Ceprkac) ===
def _load_settings() -> dict:
    settings = {"homepage": "https://www.google.com", "searchurl": "https://www.google.com/search?q={}"}
    if not os.path.exists(SETTINGS_FILE):
        return settings
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    if key == "homepage":
                        settings["homepage"] = parts[1].strip()
                    elif key == "searchurl":
                        settings["searchurl"] = parts[1].strip()
    except Exception:
        pass
    return settings


def _save_settings(homepage: str, searchurl: str):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            f.write(f"homepage={homepage}\n")
            f.write(f"searchurl={searchurl}\n")
    except Exception:
        pass


# === HISTORY (Same as Ceprkac, with case-insensitive dedup) ===
def _load_history() -> list[str]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        seen = set()
        unique = []
        for l in lines:
            key = l.lower()
            if key not in seen:
                seen.add(key)
                unique.append(l)
        return unique[-100:]
    except Exception:
        return []


def _save_history(history: list[str]):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(history) + "\n")
    except Exception:
        pass


# === CUSTOM CHROME TAB STRIP (Like Ceprkac) ===
class ChromeTab:
    def __init__(self):
        self.title: str = "New Tab"
        self.url: str = ""
        self.web_view: QWebEngineView | None = None
        self.is_loading: bool = False
        self.load_progress: int = 0
        self.last_autofill_attempt: float = 0
        self.zoom_factor: float = 1.0


class ChromeTabStrip(QWidget):
    """Custom-drawn Chrome-style tab strip matching Ceprkac."""
    tab_clicked = pyqtSignal(int)
    tab_close_clicked = pyqtSignal(int)
    new_tab_clicked = pyqtSignal()

    CLOSE_SIZE = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tabs: list[ChromeTab] = []
        self.selected_index: int = -1
        self.hover_index: int = -1
        self.hover_close_index: int = -1
        self._drag_start_pos: QPoint | None = None
        self._drag_tab_index: int = -1
        self.setFixedHeight(42)
        self.setMouseTracking(True)
        self.font = QFont("Segoe UI", 9)

    def add_tab(self, tab: ChromeTab, title: str = "New Tab") -> int:
        tab.title = title
        self.tabs.append(tab)
        self.update()
        return len(self.tabs) - 1

    def insert_tab(self, index: int, tab: ChromeTab, title: str = "New Tab"):
        tab.title = title
        self.tabs.insert(index, tab)
        if self.selected_index >= index:
            self.selected_index += 1
        self.update()

    def remove_tab(self, index: int):
        if 0 <= index < len(self.tabs):
            self.tabs.pop(index)
            if self.selected_index >= len(self.tabs):
                self.selected_index = len(self.tabs) - 1
            self.update()

    def set_tab_text(self, index: int, text: str):
        if 0 <= index < len(self.tabs):
            self.tabs[index].title = text
            self.update()

    def set_current_index(self, index: int):
        if 0 <= index < len(self.tabs):
            self.selected_index = index
            self.update()

    def _get_tab_width(self) -> int:
        if not self.tabs:
            return 200
        available = self.width() - 40 - 16
        w = available // max(len(self.tabs), 1)
        return max(60, min(240, w))

    def _get_tab_rect(self, index: int) -> QRect:
        w = self._get_tab_width()
        x = 8 + index * (w + 1)
        return QRect(x, 6, w, 34)

    def _get_close_rect(self, tab_rect: QRect) -> QRect:
        return QRect(tab_rect.right() - 20, tab_rect.y() + 9, self.CLOSE_SIZE, self.CLOSE_SIZE)

    def _get_new_tab_rect(self) -> QRect:
        w = self._get_tab_width()
        x = 8 + len(self.tabs) * (w + 1) + 4
        return QRect(x, 10, 28, 22)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.fillRect(self.rect(), Theme.TabBar)

        # New tab button (+)
        new_rect = self._get_new_tab_rect()
        painter.fillRect(new_rect, Theme.InactiveTab)
        pen = QPen(Theme.ForeLight, 1)
        painter.setPen(pen)
        cx = new_rect.center().x()
        cy = new_rect.center().y()
        painter.drawLine(cx - 4, cy, cx + 4, cy)
        painter.drawLine(cx, cy - 4, cx, cy + 4)

        # Bottom line under inactive area
        if 0 <= self.selected_index < len(self.tabs):
            sel_rect = self._get_tab_rect(self.selected_index)
            painter.setPen(QPen(Theme.ActiveTab, 2))
            painter.drawLine(0, self.height() - 1, sel_rect.left(), self.height() - 1)
            painter.drawLine(sel_rect.right(), self.height() - 1, self.width(), self.height() - 1)

        # Draw tabs
        for i in range(len(self.tabs)):
            if i == self.selected_index:
                continue
            self._draw_tab(painter, i)
        if 0 <= self.selected_index < len(self.tabs):
            self._draw_tab(painter, self.selected_index)

        painter.end()

    def _draw_tab(self, painter: QPainter, index: int):
        rect = self._get_tab_rect(index)
        tab = self.tabs[index]
        active = index == self.selected_index
        hover = index == self.hover_index and not active

        bg = Theme.ActiveTab if active else (Theme.TabHover if hover else Theme.InactiveTab)

        # Draw tab background
        painter.fillRect(QRect(rect.x(), rect.y() + 4, rect.width(), rect.height() - 6), bg)

        # Text
        text_rect = QRect(rect.x() + 12, rect.y() + 4, rect.width() - 36, rect.height() - 8)
        painter.setPen(Theme.ForeLight if active else Theme.ForeDim)
        painter.setFont(self.font)
        elided = QFontMetrics(self.font).elidedText(tab.title[:25], Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)

        # Close button X (like Ceprkac's closePen)
        if len(self.tabs) > 1 or active:
            close_rect = self._get_close_rect(rect)
            close_hover = index == self.hover_close_index
            if close_hover:
                painter.setBrush(QBrush(Theme.CloseHover))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(close_rect)
            close_pen = QPen(QColor(255, 255, 255) if close_hover else Theme.ForeDim, 1.2)
            painter.setPen(close_pen)
            m = 4
            painter.drawLine(close_rect.x() + m, close_rect.y() + m,
                             close_rect.right() - m, close_rect.bottom() - m)
            painter.drawLine(close_rect.right() - m, close_rect.y() + m,
                             close_rect.x() + m, close_rect.bottom() - m)

        # Loading indicator line at bottom (like Ceprkac's loadPen)
        if tab.is_loading:
            load_pen = QPen(Theme.Accent, 2)
            painter.setPen(load_pen)
            progress_width = max(1, (rect.width() - 8) * tab.load_progress // 100) if tab.load_progress > 0 else (rect.width() - 8) // 3
            painter.drawLine(rect.x() + 4, rect.bottom() - 2,
                             rect.x() + 4 + progress_width, rect.bottom() - 2)

    def mouseMoveEvent(self, event):
        # Tab drag-to-reorder
        if self._drag_start_pos is not None and self._drag_tab_index >= 0:
            delta = event.pos().x() - self._drag_start_pos.x()
            tab_w = self._get_tab_width() + 1
            if abs(delta) > tab_w // 2:
                direction = 1 if delta > 0 else -1
                new_idx = self._drag_tab_index + direction
                if 0 <= new_idx < len(self.tabs):
                    # Swap tabs
                    self.tabs[self._drag_tab_index], self.tabs[new_idx] = self.tabs[new_idx], self.tabs[self._drag_tab_index]
                    if self.selected_index == self._drag_tab_index:
                        self.selected_index = new_idx
                    elif self.selected_index == new_idx:
                        self.selected_index = self._drag_tab_index
                    self._drag_tab_index = new_idx
                    self._drag_start_pos = event.pos()
                    self.update()
                    self.tab_clicked.emit(self.selected_index)
            return

        old_hover = self.hover_index
        old_close = self.hover_close_index
        self.hover_index = -1
        self.hover_close_index = -1

        for i in range(len(self.tabs)):
            rect = self._get_tab_rect(i)
            if rect.contains(event.pos()):
                self.hover_index = i
                if self._get_close_rect(rect).contains(event.pos()):
                    self.hover_close_index = i
                break

        if old_hover != self.hover_index or old_close != self.hover_close_index:
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            # Middle-click to close tab (like Ceprkac)
            for i in range(len(self.tabs)):
                if self._get_tab_rect(i).contains(event.pos()):
                    self.tab_close_clicked.emit(i)
                    return
            return

        new_rect = self._get_new_tab_rect()
        if new_rect.contains(event.pos()):
            self.new_tab_clicked.emit()
            return

        for i in range(len(self.tabs)):
            rect = self._get_tab_rect(i)
            if rect.contains(event.pos()):
                if self._get_close_rect(rect).contains(event.pos()):
                    self.tab_close_clicked.emit(i)
                else:
                    self.selected_index = i
                    self.tab_clicked.emit(i)
                    # Start drag tracking
                    self._drag_start_pos = event.pos()
                    self._drag_tab_index = i
                self.update()
                break

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        self._drag_tab_index = -1


# === AD BLOCKER INTERCEPTOR (Same logic as Ceprkac) ===
class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.blocked_count = 0
        self.page_is_whitelisted = False

    def interceptRequest(self, info):
        url = info.requestUrl().toString().lower()
        try:
            host = info.requestUrl().host().lower()
            if _is_whitelisted(host):
                return
            if _is_ad_domain(host):
                info.block(True)
                self.blocked_count += 1
                return
            if any(p in url for p in ["/pagead/", "/adclick", "/aclk?", "/ptracking",
                   "/advert", "/sponsored", "/promotion", "/tracking/", "/analytics/",
                   "/collect?", "/beacon", "/pixel", "/imp?", "/impression"]):
                info.block(True)
                self.blocked_count += 1
        except Exception:
            pass


# === CUSTOM WEB PAGE FOR POPUP HANDLING (Ceprkac-style) ===
class BrowserPage(QWebEnginePage):
    def __init__(self, profile, parent=None, browser_window=None):
        super().__init__(profile, parent)
        self.browser_window = browser_window
        self._last_url = ""

    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame):
        url_str = url.toString()
        url_lower = url_str.lower()

        # Check for ad URLs
        if _is_ad_url(url_lower):
            if self.browser_window:
                self.browser_window._on_ad_blocked_navigation(self)
            return False

        # Check for auth URLs - allow them (for OAuth popups)
        if _is_auth_url(url_lower):
            return True

        self._last_url = url_str
        return True

    def createWindow(self, window_type):
        """Handle new window requests (like Ceprkac's NewWindowRequested)."""
        if not self.browser_window:
            return None

        # Get the URL being requested
        # QtWebEngine doesn't give us the URL directly, we need to check the trigger
        # For OAuth flows, we'll create a popup window
        page = BrowserPage(self.profile(), browser_window=self.browser_window)

        # Connect to detect the URL when it loads
        page.urlChanged.connect(lambda url: self.browser_window._handle_new_window_url(page, url))

        return page


# === AD ELEMENT HIDER JS (Same as Ceprkac) ===
AD_ELEMENT_HIDER_JS = r"""(function() {
    if (window.__gbrowserAdHider) return;
    window.__gbrowserAdHider = true;
    var css = document.createElement('style');
    css.textContent = [
        'ins.adsbygoogle','[id*="google_ads"]','[class*="ad-slot"]','[class*="advert"]',
        '[class*="ad-banner"]','[class*="ad-container"]','[class*="ad-wrapper"]',
        '[class*="sponsor"]','[class*="ad-placement"]','[class*="ad_"]',
        '[data-ad]','[data-adunit]','[data-ad-slot]','[data-google-query-id]',
        '.sponsored-content','.promoted','.ad-banner','.ad-container','.ad-wrapper',
        '.native-ad','.ad-unit','.ad-zone','.ad-area','.ad-block','.ad-box','.ad-frame',
        '.ad-header','.ad-footer','.ad-leaderboard','.ad-sidebar','.ad-skyscraper',
        '.ad-rectangle','.ad-interstitial','.ad-overlay','.ad-popup','.ad-modal',
        'div[id*="taboola"]','div[id*="outbrain"]','div[class*="taboola"]',
        'div[class*="outbrain"]','div[id*="zergnet"]','div[id*="revcontent"]',
        'div[id*="mgid"]','div[class*="mgid"]',
        'iframe[src*="doubleclick"]','iframe[src*="googlesyndication"]',
        'iframe[src*="googletagmanager"]','iframe[id*="google_ads"]','iframe[id*="aswift"]',
        'iframe[src*="ad"][width]','iframe[data-ad]',
        '.video-ad-overlay','.preroll-ad','.midroll-ad',
        'a[href*="doubleclick.net"]','a[href*="googleadservices"]',
        'div[aria-label="Advertisement"]','div[aria-label="advertisement"]',
        'section[aria-label="Sponsored"]',
        /* Pornhub / adult site ads */
        '.adBanner','.ad-banner','#hd-rightColAd','#pb_ad','.advertisement',
        '.mgbox','[class*="mgbox"]','div[id*="snigelAdStack"]',
        '.trafficStars','[class*="trafficStars"]','[id*="trafficStars"]',
        '[class*="exoclick"]','[id*="exoclick"]',
        'iframe[src*="trafficstars"]','iframe[src*="exoclick"]',
        'iframe[src*="trafficjunky"]','iframe[src*="adsrv"]',
        'iframe[src*="juicyads"]','iframe[src*="exosrv"]',
        'iframe[src*="tsyndicate"]','iframe[src*="realsrv"]',
        'div[class*="abovePlayer"]','div[id*="adblock"]',
        '.removeAdMessage','#removeAdblockContainer',
        /* DuckDuckGo sponsored results and self-promo */
        '.result--ad','.is-ad','[data-testid="ad"]','[data-testid="result--ad"]',
        '.badge--ad','.result__extras__url--ad',
        '.ddg-extension-hide','.js-sidebar-ads','.sidebar-modules--ads',
        '.header-aside',
        /* Google sponsored results */
        '#tads','#tadsb','#bottomads','.commercial-unit-desktop-top',
        '.commercial-unit-desktop-rhs','.cu-container',
        'div[data-text-ad]','div[data-hveid] .uEierd',
        /* Bing sponsored results */
        '.b_ad','.b_adSlug','li.b_ad','#b_results > .b_ad',
        /* Yahoo sponsored results */
        '.searchCenterTopAds','.searchCenterBottomAds','.compDlink',
        /* Reddit promoted posts (GSecurity Ad Shield) */
        'shreddit-ad-post','[data-testid="ad-post"]','[data-testid="promoted-post"]',
        'div[data-promoted="true"]','.promotedlink','.sponsorshipbox','.sponsor-logo',
        'faceplate-tracker[source="ad"]','faceplate-tracker[noun="ad"]',
        '[data-testid="sidebar-ad"]','[data-testid="subreddit-sidebar-ad"]',
        '.sidebar-ad','div[class*="promotedlink"]','.premium-banner-outer',
        '[data-testid="premium-upsell"]',
        'shreddit-experience-tree[bundlename*="ad"]','shreddit-experience-tree[bundlename*="Ad"]',
        '.thing.promoted','.thing.stickied.promotedlink',
        /* LinkedIn ads */
        '[data-ad-banner-id]','[data-is-sponsored="true"]',
        '.ad-banner-container','.ads-container',
        /* Twitch ads */
        '[data-a-target="video-ad-label"]','.video-ad','.advertisement-banner',
        '[data-test-selector="ad-banner-default-id"]','.stream-display-ad',
        /* TikTok ads */
        '[class*="DivAdBanner"]','[data-e2e="ad"]'
    ].join(',') + '{display:none!important;height:0!important;min-height:0!important;overflow:hidden!important}';
    (document.head || document.documentElement).appendChild(css);
    var sels = [
        'ins.adsbygoogle','iframe[src*="doubleclick"]','iframe[src*="googlesyndication"]',
        'iframe[src*="googletagmanager"]','iframe[id*="google_ads"]','iframe[id*="aswift"]',
        '[id*="google_ads"]','[class*="ad-slot"]','[class*="advert"]','[class*="ad-banner"]',
        '[class*="ad-container"]','[class*="ad-wrapper"]','[class*="sponsor"]',
        '[data-ad]','[data-adunit]','[data-ad-slot]','[data-google-query-id]',
        '.sponsored-content','.promoted','.ad-banner','.ad-container','.ad-wrapper',
        '.native-ad','.ad-unit','.ad-zone','.ad-area','.ad-block','.ad-box','.ad-frame',
        'div[id*="taboola"]','div[id*="outbrain"]','div[class*="taboola"]',
        'div[class*="outbrain"]','div[id*="zergnet"]','div[id*="revcontent"]',
        'div[id*="mgid"]','div[class*="mgid"]',
        '.video-ad-overlay','.preroll-ad','.midroll-ad',
        'div[aria-label="Advertisement"]','div[aria-label="advertisement"]',
        /* Search engine sponsored results */
        '.result--ad','.is-ad','[data-testid="ad"]','[data-testid="result--ad"]',
        '.badge--ad','.ddg-extension-hide','.js-sidebar-ads','.header-aside',
        '#tads','#tadsb','#bottomads','.commercial-unit-desktop-top',
        '.commercial-unit-desktop-rhs','div[data-text-ad]',
        '.b_ad','.b_adSlug','li.b_ad',
        '.searchCenterTopAds','.searchCenterBottomAds',
        /* Reddit (GSecurity Ad Shield) */
        'shreddit-ad-post','[data-testid="ad-post"]','[data-testid="promoted-post"]',
        'div[data-promoted="true"]','.promotedlink','.sponsorshipbox','.sponsor-logo',
        '#ad-frame','#ad_main',
        'faceplate-tracker[source="ad"]','faceplate-tracker[noun="ad"]',
        '[data-testid="sidebar-ad"]','[data-testid="subreddit-sidebar-ad"]',
        'shreddit-experience-tree[bundlename*="ad"]','shreddit-experience-tree[bundlename*="Ad"]',
        '.premium-banner-outer','[data-testid="premium-upsell"]',
        /* LinkedIn */
        '[data-ad-banner-id]','[data-is-sponsored="true"]',
        '.ad-banner-container','.ads-container',
        /* Twitch */
        '[data-a-target="video-ad-label"]','.video-ad','.advertisement-banner',
        '[data-test-selector="ad-banner-default-id"]','.stream-display-ad',
        /* TikTok */
        '[class*="DivAdBanner"]','[data-e2e="ad"]'
    ];
    function scrub() {
        for (var i = 0; i < sels.length; i++) {
            try {
                var els = document.querySelectorAll(sels[i]);
                for (var j = 0; j < els.length; j++) {
                    if (els[j] && els[j].parentElement) els[j].remove();
                }
            } catch(e) {}
        }
        try {
            document.querySelectorAll('article, [data-testid="post-container"], .thing').forEach(function(post) {
                var badges = post.querySelectorAll('span, faceplate-tracker, [slot="credit-bar"], .tagline');
                for (var k = 0; k < badges.length; k++) {
                    var text = (badges[k].textContent || '').trim().toLowerCase();
                    if (text === 'promoted' || text === 'sponsored') { post.remove(); break; }
                }
            });
            document.querySelectorAll('shreddit-post').forEach(function(post) {
                if (post.hasAttribute('is-promoted') || post.getAttribute('post-type') === 'promoted') post.remove();
            });
        } catch(e) {}
        try {
            document.querySelectorAll('div[role="article"], div[role="feed"] > div').forEach(function(article) {
                var spans = article.querySelectorAll('span');
                for (var k = 0; k < spans.length; k++) {
                    if ((spans[k].textContent || '').trim().toLowerCase() === 'sponsored') {
                        article.style.display = 'none'; break;
                    }
                }
            });
        } catch(e) {}
        try {
            document.querySelectorAll('article, [data-testid="placementTracking"]').forEach(function(el) {
                var text = (el.textContent || '').toLowerCase();
                if (/\bpromoted\b/.test(text) || /\bad\s*·/.test(text) || el.matches('[data-testid="placementTracking"]')) {
                    el.style.display = 'none';
                }
            });
        } catch(e) {}
        try {
            document.querySelectorAll('article').forEach(function(a) {
                if (/\bsponsored\b/i.test(a.textContent || '')) a.style.display = 'none';
            });
        } catch(e) {}
    }
    scrub();
    setInterval(scrub, 1500);
    new MutationObserver(scrub).observe(document.documentElement, {childList:true, subtree:true});
})()"""

YOUTUBE_AD_BLOCKER_JS = r"""(function() {
    if (window.__gbrowserYtAdBlock) return;
    window.__gbrowserYtAdBlock = true;
    var s = document.createElement('style');
    s.textContent = 'ytd-display-ad-renderer,ytd-ad-slot-renderer,ytd-promoted-video-renderer,ytd-promoted-sparkles-web-renderer,ytd-promoted-sparkles-text-search-renderer,ytd-banner-promo-renderer,ytd-statement-banner-renderer,ytd-in-feed-ad-layout-renderer,ytd-masthead-ad-renderer,ytd-primetime-promo-renderer,ytd-compact-promoted-video-renderer,ytd-action-companion-ad-renderer,ytd-mealbar-promo-renderer,ytd-enforcement-message-view-model,ytd-engagement-panel-section-list-renderer[target-id=engagement-panel-ads],#masthead-ad,#player-ads,.video-ads,.ytp-ad-module,.ytp-ad-overlay-container,.ytp-ad-player-overlay,.ytp-ad-action-interstitial,.ytp-ad-image-overlay,.ytp-ad-text-overlay,.ytp-ad-skip-ad-slot,.ad-showing .ytp-ad-module,ytd-search-pyv-renderer,ytd-movie-offer-module-renderer,tp-yt-paper-dialog:has(#dismiss-button),ytd-popup-container:has(a[href*="/premium"]),ytd-rich-item-renderer:has(ytd-ad-slot-renderer),ytd-rich-item-renderer:has(ytd-display-ad-renderer),ytd-rich-item-renderer:has(ytd-promoted-video-renderer),ytd-rich-item-renderer:has(ytd-promoted-sparkles-web-renderer),ytd-rich-section-renderer:has(ytd-ad-slot-renderer){display:none!important}';
    (document.head||document.documentElement).appendChild(s);
    var adKeys=['adPlacements','adSlots','playerAds','adBreakHeartbeatParams','ad3Module','adSafetyReason','adLoggingData','showAdSlots','adBreakParams','adBreakStatus','adVideoId','adLayoutLoggingData','instreamAdPlayerOverlayRenderer','adPlacementConfig','adVideoStitcherConfig','promotedSparklesWebRenderer','promotedSparklesTextSearchRenderer','promotedVideoRenderer','sponsoredCardRenderer','adSlotRenderer','displayAdRenderer','inFeedAdLayoutRenderer','mastheadAdRenderer','compactPromotedVideoRenderer','actionCompanionAdRenderer','bannerPromoRenderer','statementBannerRenderer','primeTimePromoRenderer','searchPyvRenderer','movieOfferModuleRenderer','adPlacementRenderer','sparklesAdRenderer'];
    function stripAds(o,d){if(!o||typeof o!=='object'||d>12)return;for(var i=0;i<adKeys.length;i++)if(o.hasOwnProperty(adKeys[i]))delete o[adKeys[i]];var k=Object.keys(o);for(var j=0;j<k.length;j++){var key=k[j],val=o[key];if(Array.isArray(val)){for(var m=val.length-1;m>=0;m--){var item=val[m];if(item&&typeof item==='object'){var ik=Object.keys(item);for(var n=0;n<ik.length;n++){if(/^(ad|promoted|sponsor)/i.test(ik[n])){val.splice(m,1);break;}}}}}else if(val&&typeof val==='object')stripAds(val,d+1);}}
    var op=JSON.parse;JSON.parse=function(){var r=op.apply(this,arguments);try{if(r&&typeof r==='object')stripAds(r,0);}catch(e){}return r;};
    ['ytInitialPlayerResponse','ytInitialData','ytcfg'].forEach(function(p){var v=window[p];try{Object.defineProperty(window,p,{configurable:true,get:function(){return v;},set:function(n){if(n&&typeof n==='object')stripAds(n,0);v=n;}});if(v)window[p]=v;}catch(e){}});
    var adS=['.video-ads','.ytp-ad-module','.ytp-ad-overlay-container','.ytp-ad-player-overlay','.ytp-ad-action-interstitial','.ytp-ad-image-overlay','.ytp-ad-text-overlay','#player-ads','#masthead-ad','ytd-display-ad-renderer','ytd-ad-slot-renderer','ytd-promoted-video-renderer','ytd-promoted-sparkles-web-renderer','ytd-banner-promo-renderer','ytd-in-feed-ad-layout-renderer','ytd-mealbar-promo-renderer','ytd-enforcement-message-view-model','ytd-search-pyv-renderer','ytd-movie-offer-module-renderer','ytd-compact-promoted-video-renderer','ytd-action-companion-ad-renderer','ytd-primetime-promo-renderer','ytd-masthead-ad-renderer'];
    var skS=['.ytp-ad-skip-button','.ytp-skip-ad-button','.ytp-ad-skip-button-modern','.ytp-skip-ad-button__text','button[class*="skip"]','.ytp-ad-overlay-close-button','.ytp-ad-skip-button-slot'];
    var sponsorWords=['sponsored','sponzorirano','gesponsert','sponsorisé','patrocinado','sponsorizzato','gesponsord','\u0441\u043f\u043e\u043d\u0441\u0438\u0440\u0443\u0435\u043c\u0430\u044f','\u30b9\u30dd\u30f3\u30b5\u30fc','\u8d5e\u52a9','\uad11\uace0','reklam','promowane','sponzorované','szponzorált','annonce','reklama','hirdetés','\u0440\u0435\u043a\u043b\u0430\u043c\u0430','commandité','gesponsord','publicidad','pubblicità','anúncio','reklame','sponzorováno','sponzorirane','\u0441\u043f\u043e\u043d\u0437\u043e\u0440\u0438\u0440\u0430\u043d\u043e'];
    function isSponsoredText(t){t=t.trim().toLowerCase();for(var i=0;i<sponsorWords.length;i++){if(t===sponsorWords[i])return true;}return false;}
    function scrub(){for(var i=0;i<adS.length;i++)document.querySelectorAll(adS[i]).forEach(function(e){var p=e.closest('ytd-rich-item-renderer,ytd-rich-section-renderer,ytd-reel-shelf-renderer');if(p)p.remove();else e.remove();});for(var j=0;j<skS.length;j++)document.querySelectorAll(skS[j]).forEach(function(b){if(b.click)b.click();});try{document.querySelectorAll('ytd-rich-item-renderer,ytd-rich-section-renderer').forEach(function(item){if(item.querySelector('ytd-ad-slot-renderer,ytd-display-ad-renderer,ytd-promoted-video-renderer,ytd-promoted-sparkles-web-renderer,ytd-in-feed-ad-layout-renderer')){item.remove();return;}var badges=item.querySelectorAll('span.ytd-badge-supported-renderer,ytd-badge-supported-renderer span,div.ytd-badge-supported-renderer,ytd-badge-supported-renderer,[class*="badge"],.badge,.badge-style-type-ad,span[aria-label]');for(var k=0;k<badges.length;k++){if(isSponsoredText(badges[k].textContent||'')){item.remove();return;}}var metas=item.querySelectorAll('#metadata-line span,#byline-container span,yt-formatted-string.ytd-channel-name');for(var m=0;m<metas.length;m++){if(isSponsoredText(metas[m].textContent||'')){item.remove();return;}}});}catch(e){}try{document.querySelectorAll('ytd-video-renderer,ytd-compact-video-renderer').forEach(function(item){var badges=item.querySelectorAll('span.ytd-badge-supported-renderer,ytd-badge-supported-renderer span,[class*="badge"]');for(var k=0;k<badges.length;k++){if(isSponsoredText(badges[k].textContent||'')){item.remove();return;}}});}catch(e){}var p=document.querySelector('.html5-video-player'),v=document.querySelector('video');if(p&&v&&(p.classList.contains('ad-showing')||p.classList.contains('ad-interrupting'))){if(Number.isFinite(v.duration)&&v.duration>0){v.currentTime=Math.max(0,v.duration-0.1);}v.muted=true;v.playbackRate=16;try{v.play();}catch(e){}p.classList.remove('ad-showing');p.classList.remove('ad-interrupting');p.classList.remove('ad-created');document.querySelectorAll('.ytp-ad-skip-button,.ytp-skip-ad-button,.ytp-ad-skip-button-modern').forEach(function(b){b.click();});setTimeout(function(){v.muted=false;v.playbackRate=1;},500);}document.querySelectorAll('ytd-rich-item-renderer').forEach(function(el){var hasAd=!!el.querySelector('ytd-ad-slot-renderer,ytd-display-ad-renderer,ytd-promoted-video-renderer,ytd-promoted-sparkles-web-renderer');if(hasAd){el.remove();return;}});document.querySelectorAll('tp-yt-paper-dialog').forEach(function(d){var t=(d.textContent||'').toLowerCase();if(t.includes('ad blocker')||t.includes('allow ads')){var b=d.querySelector('#dismiss-button,.dismiss-button,button');if(b&&b.click)b.click();d.remove();}});}
    scrub();setInterval(scrub,200);new MutationObserver(scrub).observe(document.documentElement,{childList:true,subtree:true});
})()"""

# YouTube main-world ad blocker — injected via <script> tag to run in main world
# before any page scripts. Intercepts JSON.parse, ytInitialData, fetch responses.
# Ported from Ceprkac's BuildYouTubeMainWorldCode().
YOUTUBE_MAIN_WORLD_JS = (
    "(function(){"
    "var h=location.hostname.toLowerCase();"
    "if(h!=='youtube.com'&&h!=='www.youtube.com'&&h!=='m.youtube.com'&&h!=='music.youtube.com'&&!h.endsWith('.youtube.com'))return;"
    "if(/accounts\\.google|login\\.microsoft|appleid\\.apple|auth0\\.com|clerk\\.|oauth/.test(h))return;"
    "if(window.__gbrowserYtMain)return;window.__gbrowserYtMain=true;"
    "var adKeys=['adPlacements','adSlots','playerAds','adBreakHeartbeatParams','ad3Module',"
    "'adSafetyReason','adLoggingData','showAdSlots','adBreakParams','adBreakStatus',"
    "'adVideoId','adLayoutLoggingData','instreamAdPlayerOverlayRenderer',"
    "'adPlacementConfig','adVideoStitcherConfig',"
    "'promotedSparklesWebRenderer','promotedSparklesTextSearchRenderer',"
    "'promotedVideoRenderer','sponsoredCardRenderer','adSlotRenderer',"
    "'displayAdRenderer','inFeedAdLayoutRenderer','mastheadAdRenderer',"
    "'compactPromotedVideoRenderer','actionCompanionAdRenderer',"
    "'bannerPromoRenderer','statementBannerRenderer','primeTimePromoRenderer',"
    "'searchPyvRenderer','movieOfferModuleRenderer','adPlacementRenderer','sparklesAdRenderer'];"
    "function strip(o,d){if(!o||typeof o!=='object'||d>15)return;"
    "for(var i=0;i<adKeys.length;i++)if(o.hasOwnProperty(adKeys[i]))delete o[adKeys[i]];"
    "var k=Object.keys(o);for(var j=0;j<k.length;j++){"
    "var key=k[j],val=o[key];"
    "if(Array.isArray(val)){for(var m=val.length-1;m>=0;m--){"
    "var item=val[m];if(item&&typeof item==='object'){"
    "var ik=Object.keys(item);var isAd=false;"
    "for(var n=0;n<ik.length;n++){"
    "if(/^(ad|promoted|sponsor)/i.test(ik[n])){isAd=true;break;}}"
    "if(!isAd&&item.richItemRenderer&&item.richItemRenderer.content){"
    "var ck=Object.keys(item.richItemRenderer.content);"
    "for(var c=0;c<ck.length;c++){if(/^(ad|promoted|sponsor)/i.test(ck[c])){isAd=true;break;}}}"
    "if(!isAd){try{var js=JSON.stringify(item);"
    "if(/\"style\":\"BADGE_STYLE_TYPE_AD\"/.test(js)||"
    "/\"label\":\"(?:Sponsored|Sponzorirano|Gesponsert|Sponsoris\\u00e9|Patrocinado|Sponsorizzato|Gesponsord|\\u0420\\u0435\\u043a\\u043b\\u0430\\u043c\\u0430|\\u30b9\\u30dd\\u30f3\\u30b5\\u30fc|\\u8d5e\\u52a9|\\uad11\\uace0|Reklam|Promowane|Sponzorovan\\u00e9|Szponzor\\u00e1lt|Annonce|Reklama|Hirdet\\u00e9s|Commandit\\u00e9|Publicidad|Pubblicit\\u00e0|An\\u00fancio|Reklame|Sponzorirane|\\u0421\\u043f\\u043e\\u043d\\u0437\\u043e\\u0440\\u0438\\u0440\\u0430\\u043d\\u043e)\"/.test(js))"
    "{isAd=true;}}catch(e){}}"
    "if(isAd){val.splice(m,1);}"
    "else{strip(item,d+1);}"
    "}}"
    "}else if(val&&typeof val==='object')strip(val,d+1);}}"
    "var op=JSON.parse;JSON.parse=function(){var r=op.apply(this,arguments);"
    "try{if(r&&typeof r==='object')strip(r,0);}catch(e){}return r;};"
    "['ytInitialPlayerResponse','ytInitialData'].forEach(function(p){var v=window[p];"
    "try{Object.defineProperty(window,p,{configurable:true,"
    "get:function(){return v;},set:function(n){if(n&&typeof n==='object')strip(n,0);v=n;}});"
    "if(v)window[p]=v;}catch(e){}});"
    "var oFetch=window.fetch;window.fetch=function(){var args=arguments;"
    "var url=typeof args[0]==='string'?args[0]:(args[0]&&args[0].url?args[0].url:'');"
    "if(!/youtubei\\/v1\\/(browse|search|next|player|reel)/.test(url))return oFetch.apply(this,args);"
    "return oFetch.apply(this,args).then(function(resp){"
    "if(!resp||!resp.ok)return resp;"
    "return resp.clone().text().then(function(txt){"
    "try{var data=op.call(JSON,txt);strip(data,0);"
    "return new Response(JSON.stringify(data),{status:resp.status,statusText:resp.statusText,headers:resp.headers});"
    "}catch(e){return resp;}});});};"
    "})()"
)

# Wrapper that injects YOUTUBE_MAIN_WORLD_JS via <script> tag into the main world
YOUTUBE_MAIN_WORLD_INJECTOR_JS = (
    "(function(){if(location.hostname.indexOf('youtube')===-1)return;"
    "var sc=document.createElement('script');"
    "sc.textContent='" + YOUTUBE_MAIN_WORLD_JS.replace("\\", "\\\\").replace("'", "\\'") + "';"
    "(document.head||document.documentElement).appendChild(sc);sc.remove();})()"
)

CHECK_LOGIN_FIELDS_JS = r"""(function() {
    var pw = document.querySelector('input[type="password"]');
    var emailOrUser = document.querySelector(
        'input[type="email"], input[type="tel"], input[name="email"], input[name="username"], ' +
        'input[name="login"], input[name="user"], input[autocomplete="username"], ' +
        'input[autocomplete="email"], input[aria-label*="mail" i], input[aria-label*="user" i], ' +
        'input[aria-label*="phone" i], input[aria-label*="login" i], input[aria-label*="Email"], ' +
        'input[aria-label*="Phone"]'
    );
    if (!emailOrUser) {
        var all = document.querySelectorAll('input[type="text"], input:not([type])');
        for (var i = 0; i < all.length; i++) {
            if (all[i].offsetParent !== null && all[i].offsetWidth > 0) { emailOrUser = all[i]; break; }
        }
    }
    if (pw && emailOrUser) return 'both';
    if (pw) return 'pwonly';
    if (emailOrUser) return 'useronly';
    return 'none';
})()"""


def _make_fill_js(username: str, password: str) -> str:
    esc_u = json.dumps(username)
    esc_p = json.dumps(password)
    return f"""(function(){{
    var u={esc_u}, p={esc_p};
    var pw = document.querySelector('input[type="password"]');
    if (!pw) return;
    var form = pw.closest('form') || document.body;
    var user = form.querySelector([
        'input[type="email"]',
        'input[name="email"]',
        'input[name="username"]',
        'input[name="login"]',
        'input[name="user"]',
        'input[autocomplete="username"]',
        'input[autocomplete="email"]',
        'input[type="text"][name*="user"]',
        'input[type="text"][name*="login"]',
        'input[type="text"][name*="email"]',
        'input[type="text"][autocomplete*="user"]',
        'input[aria-label*="mail"]',
        'input[aria-label*="user"]',
        'input[aria-label*="login"]',
        'input[aria-label*="phone"]'
    ].join(', '));
    if (!user) {{
        var inputs = form.querySelectorAll('input[type="text"], input[type="email"], input:not([type])');
        for (var i = 0; i < inputs.length; i++) {{
            var inp = inputs[i];
            if (inp !== pw && inp.offsetParent !== null) {{ user = inp; break; }}
        }}
    }}
    if (user) {{
        var nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSet.call(user, u);
        user.dispatchEvent(new Event('input', {{bubbles:true}}));
        user.dispatchEvent(new Event('change', {{bubbles:true}}));
    }}
    var nativeSet2 = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeSet2.call(pw, p);
    pw.dispatchEvent(new Event('input', {{bubbles:true}}));
    pw.dispatchEvent(new Event('change', {{bubbles:true}}));
}})()"""


def _make_fill_username_js(username: str) -> str:
    esc_u = json.dumps(username)
    return f"""(function(){{
    var u={esc_u};
    var user = document.querySelector(
        'input[type="email"], input[type="tel"], input[name="email"], input[name="username"], ' +
        'input[name="login"], input[name="user"], input[autocomplete="username"], ' +
        'input[autocomplete="email"], input[aria-label*="mail" i], input[aria-label*="user" i], ' +
        'input[aria-label*="phone" i], input[aria-label*="login" i], input[aria-label*="Email"], ' +
        'input[aria-label*="Phone"]'
    );
    if (!user) {{
        var all = document.querySelectorAll('input[type="text"], input:not([type])');
        for (var i = 0; i < all.length; i++) {{
            if (all[i].offsetParent !== null && all[i].offsetWidth > 0) {{ user = all[i]; break; }}
        }}
    }}
    if (user) {{
        var nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSet.call(user, u);
        user.dispatchEvent(new Event('input', {{bubbles:true}}));
        user.dispatchEvent(new Event('change', {{bubbles:true}}));
        user.dispatchEvent(new Event('blur', {{bubbles:true}}));
    }}
}})()"""


# === DOWNLOAD ITEM TRACKER ===
class DownloadItem:
    def __init__(self, filename: str):
        self.filename = filename
        self.received = 0
        self.total = 0
        self.status = "Downloading"


# === HISTORY DIALOG ===
class HistoryDialog(QDialog):
    """Simple dialog showing last 100 history URLs."""
    def __init__(self, history: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browsing History")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(
            f"QDialog {{ background: rgb({Theme.ActiveTab.red()},{Theme.ActiveTab.green()},{Theme.ActiveTab.blue()}); color: white; }}")
        self._selected_url: str = ""
        layout = QVBoxLayout(self)

        self._list = QListWidget()
        self._list.setStyleSheet(
            f"QListWidget {{ background: rgb({Theme.TitleBar.red()},{Theme.TitleBar.green()},{Theme.TitleBar.blue()});"
            f"color: white; border: 1px solid rgb({Theme.Border.red()},{Theme.Border.green()},{Theme.Border.blue()}); }}"
            f"QListWidget::item:selected {{ background: rgb({Theme.Accent.red()},{Theme.Accent.green()},{Theme.Accent.blue()}); color: black; }}")
        for url in reversed(history[-100:]):
            self._list.addItem(url)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet(
            f"QPushButton {{ background: rgb({Theme.CloseHover.red()},{Theme.CloseHover.green()},{Theme.CloseHover.blue()});"
            f"color: white; border: none; border-radius: 4px; padding: 6px 16px; }}")
        clear_btn.clicked.connect(lambda: self.done(2))  # code 2 = clear
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            f"QPushButton {{ background: rgb({Theme.Accent.red()},{Theme.Accent.green()},{Theme.Accent.blue()});"
            f"color: black; border: none; border-radius: 4px; padding: 6px 16px; }}")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _on_item_double_clicked(self, item):
        self._selected_url = item.text()
        self.accept()

    def selected_url(self) -> str:
        return self._selected_url


# === DOWNLOAD MANAGER DIALOG ===
class DownloadManagerDialog(QDialog):
    """Dialog showing recent downloads with progress."""
    def __init__(self, downloads: list[DownloadItem], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloads")
        self.setMinimumSize(500, 350)
        self.setStyleSheet(
            f"QDialog {{ background: rgb({Theme.ActiveTab.red()},{Theme.ActiveTab.green()},{Theme.ActiveTab.blue()}); color: white; }}")
        layout = QVBoxLayout(self)

        self._list = QListWidget()
        self._list.setStyleSheet(
            f"QListWidget {{ background: rgb({Theme.TitleBar.red()},{Theme.TitleBar.green()},{Theme.TitleBar.blue()});"
            f"color: white; border: 1px solid rgb({Theme.Border.red()},{Theme.Border.green()},{Theme.Border.blue()}); }}")
        for dl in reversed(downloads):
            if dl.total > 0:
                pct = int(dl.received * 100 / dl.total)
                text = f"{dl.filename}  —  {pct}%  ({dl.status})"
            else:
                text = f"{dl.filename}  —  {dl.received} bytes  ({dl.status})"
            self._list.addItem(text)
        layout.addWidget(self._list, 1)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(
            f"QPushButton {{ background: rgb({Theme.Accent.red()},{Theme.Accent.green()},{Theme.Accent.blue()});"
            f"color: black; border: none; border-radius: 4px; padding: 6px 16px; }}")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


# === MAIN BROWSER WINDOW (Logic-matched to Ceprkac) ===
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self._tabs: list[ChromeTab] = []
        self._active_tab_index: int = -1
        self._home_url: str = "https://www.google.com"
        self._search_template: str = "https://www.google.com/search?q={}"
        self._bookmarks: list[BookmarkNode] = []
        self._history: list[str] = []
        self._passwords = PasswordManager()
        self._ad_blocker = AdBlockInterceptor()
        self._devtools_windows: list[QWebEngineView] = []
        self._download_windows: list[QWidget] = []
        self._downloads: list[DownloadItem] = []
        self._closed_tabs: list[str] = []  # Stack of closed tab URLs (max 20)
        self._cached_main_world_js: str = ""  # Cached blocker JS
        self._last_bookmark_hash: int = 0  # For incremental bookmark bar updates
        self._profile = QWebEngineProfile("GBrowserProfile", self)
        self._profile.setUrlRequestInterceptor(self._ad_blocker)
        self._profile.downloadRequested.connect(self._on_download_requested)

        self._build_cached_main_world_js()
        self._init_ui()
        self._apply_dark_titlebar()
        self._load_initial_settings()
        self._bookmarks = _load_bookmarks()
        self._history = _load_history()
        _load_blocklist_file(_resource_path("blocklist.txt"))
        self._build_cached_main_world_js()  # Rebuild after blocklist loaded

        # Show search engine picker on first launch
        if not os.path.exists(SETTINGS_FILE):
            self._show_search_engine_picker()

        self._add_new_tab(self._home_url)
        self._refresh_bookmarks_bar()
        self._update_completer_data()

    def _build_cached_main_world_js(self):
        """Build the main-world blocker JS string ONCE (perf improvement #14)."""
        top_domains = [d for d in BLOCKED_AD_DOMAINS if '*' not in d and 3 < len(d) < 60][:15000]
        domain_list = ','.join(f'"{d}"' for d in top_domains)
        wl_domains = "','".join([
            "google.com","youtube.com","accounts.google.com","apis.google.com","ssl.gstatic.com",
            "gstatic.com","discord.com","discordapp.com","github.com","paypal.com","ebay.com",
            "apple.com","icloud.com","mediafire.com","login.microsoftonline.com","login.live.com",
            "pay.google.com","gog.com","steampowered.com","steamcommunity.com","epicgames.com",
            "ea.com","origin.com","ubisoft.com","blizzard.com","battle.net","riotgames.com",
            "xbox.com","playstation.com","nintendo.com","twitch.tv","chase.com","bankofamerica.com",
            "wellsfargo.com","citibank.com","capitalone.com","revolut.com","wise.com","stripe.com","n26.com"
        ])
        self._cached_main_world_js = (
            "(function(){if(window.__gFB)return;window.__gFB=1;"
            f"var b=new Set([{domain_list}]);"
            f"var wl=new Set(['{wl_domains}']);"
            "function isWl(h){while(h){if(wl.has(h))return 1;var i=h.indexOf('.');if(i<0)break;h=h.substr(i+1);}return 0};"
            "function chk(u){try{if(isWl(location.hostname))return 0;var l=u.toLowerCase();var h=new URL(l).hostname;"
            "if(isWl(h))return 0;while(h){if(b.has(h))return 1;var i=h.indexOf('.');if(i<0)break;h=h.substr(i+1);}"
            "if(/(\\/ads?\\/|\\/ad[sx]?\\b|\\/pagead\\/|\\/ptracking|\\/advert|\\/sponsored|\\/promotion|\\/tracking\\/|\\/analytics\\/|\\/collect\\?|\\/beacon|\\/pixel|\\/imp\\?|\\/impression|\\/click\\?|ad_banner|ad_frame|sponsored_content|promo_banner|[?&](ad|ads|adunit|adformat|adtag)=)/i.test(l))return 1;"
            "if(/(?:\\/(?:adcontent|img\\/adv|web-ad|iframead|contentad|ad\\/image|video-ad|stats\\/event|xtclicks|adscript|bannerad|googlead|adhandler|adimages|adconfig|tracking\\/track|tracker\\/track|adrequest|nativead|adman|advertisement|adframe|adcontrol|adoverlay|adserver|adsense|google-ads|ad-banner|banner-ad|adplacement|adblockdetect|advertising|admanagement|adprovider|adrotation|adunit|adcall|adlog|adcount|adserve|adsrv|adsys|adtrack|adview|adwidget|adzone|sidebar-ads|footer-ads|top-ads|bottom-ads|ads\\.php|ad\\.js|ad\\.css))/i.test(l))return 1;"
            "if(/\\/api\\/stats\\/(ads|atr)/i.test(l))return 1;"
            "var hh=new URL(l).hostname;"
            "if(/^(?:.*[-_.])?(ads?|adv(ert(s|ising)?)?|banners?|track(er|ing|s)?|beacons?|doubleclick|adservice|adnxs|adtech|googleads|gads|adwords|partner|sponsor(ed)?|click(s|bank|tale|through)?|pop(up|under)s?|promo(tion)?|market(ing|er)?|affiliates?|metrics?|stat(s|counter|istics)?|analytics?|pixels?|campaign|traff(ic|iq)|monetize|syndicat(e|ion)|revenue|yield|impress(ion)?s?|conver(sion|t)?|audience|target(ing)?|behavior|profil(e|ing)|telemetry|survey|outbrain|taboola|quantcast|scorecard|omniture|comscore|krux|bluekai|exelate|adform|adroll|rubicon|vungle|inmobi|flurry|mixpanel|heap|amplitude|optimizely|bizible|pardot|hubspot|marketo|eloqua|media(math|net)|criteo|appnexus|turn|adbrite|admob|adsonar|adscale|zergnet|revcontent|mgid|nativeads|contentad|displayads|bannerflow|adblade|adcolony|chartbeat|newrelic|pingdom|kissmetrics|tradedesk|bidder|auction|rtb|programmatic|interstitial|overlay|trafficjunky|trafficstars|exoclick|juicyads|realsrv|magsrv)\\./i.test(hh))return 1;"
            "if(/^(?:adcreative(s)?|imageserv|media(mgr)?|stats|switch|track(2|er)?|view|ads?\\d{0,3}|banners?\\d{0,3}|clicks?\\d{0,3}|count(er)?\\d{0,3}|servedby\\d{0,3}|toolbar\\d{0,3}|pageads\\d{0,3}|pops\\d{0,3}|promos?\\d{0,3})\\./i.test(hh))return 1;"
            "if(/(?:\\/(1|blank|b|clear|pixel|transp|spacer)\\.gif|\\.swf)$/i.test(l))return 1;"
            "return 0}catch(e){return 0}};"
            "var F=fetch;window.fetch=function(a,o){var u=typeof a==='string'?a:a&&a.url?a.url:'';if(chk(u))return Promise.reject(new TypeError('blocked'));return F.apply(this,arguments)};"
            "var X=XMLHttpRequest.prototype.open;XMLHttpRequest.prototype.open=function(){var u=arguments[1]||'';if(typeof u==='string'&&chk(u)){this.__blk=1;return}return X.apply(this,arguments)};"
            "var S=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.send=function(){if(this.__blk)return;return S.apply(this,arguments)};"
            "})()"
        )

    def _init_ui(self):
        self.setWindowTitle("GBrowser")
        self.setMinimumSize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom Chrome-style tab strip
        self._tab_strip = ChromeTabStrip()
        self._tab_strip.tab_clicked.connect(self._on_tab_clicked)
        self._tab_strip.tab_close_clicked.connect(self._on_tab_close_clicked)
        self._tab_strip.new_tab_clicked.connect(lambda: self._add_new_tab(self._home_url))
        layout.addWidget(self._tab_strip)

        # Navigation toolbar
        nav = QWidget()
        nav.setStyleSheet(f"background: rgb({Theme.Toolbar.red()},{Theme.Toolbar.green()},{Theme.Toolbar.blue()}); padding: 4px;")
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(6)

        btn_style = (f"QPushButton {{ background: transparent; color: white; border: none; padding: 4px 8px; font-size: 14px; }}"
                     f"QPushButton:hover {{ background: rgb({Theme.TabHover.red()},{Theme.TabHover.green()},{Theme.TabHover.blue()}); border-radius: 4px; }}")

        self._back_btn = QPushButton("\u2190")
        self._back_btn.setStyleSheet(btn_style)
        self._back_btn.setToolTip("Back")
        self._back_btn.clicked.connect(self._go_back)
        nav_layout.addWidget(self._back_btn)

        self._fwd_btn = QPushButton("\u2192")
        self._fwd_btn.setStyleSheet(btn_style)
        self._fwd_btn.setToolTip("Forward")
        self._fwd_btn.clicked.connect(self._go_forward)
        nav_layout.addWidget(self._fwd_btn)

        self._reload_btn = QPushButton("\u21bb")
        self._reload_btn.setStyleSheet(btn_style)
        self._reload_btn.setToolTip("Reload")
        self._reload_btn.clicked.connect(self._reload)
        nav_layout.addWidget(self._reload_btn)

        self._address = QLineEdit()
        self._address.setStyleSheet(
            f"QLineEdit {{ background: rgb({Theme.AddressBox.red()},{Theme.AddressBox.green()},{Theme.AddressBox.blue()});"
            f"color: white; border: 1px solid rgb({Theme.Border.red()},{Theme.Border.green()},{Theme.Border.blue()});"
            f"border-radius: 16px; padding: 4px 12px; font-size: 13px; }}"
        )
        self._address.returnPressed.connect(self._on_address_enter)
        nav_layout.addWidget(self._address, 1)

        # Address bar autocomplete (#11)
        self._completer = QCompleter([], self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setMaxVisibleItems(8)
        self._address.setCompleter(self._completer)

        self._bookmark_btn = QPushButton("\u2606")
        self._bookmark_btn.setStyleSheet(btn_style)
        self._bookmark_btn.setToolTip("Add bookmark (Ctrl+D)")
        self._bookmark_btn.clicked.connect(self._toggle_bookmark)
        nav_layout.addWidget(self._bookmark_btn)

        self._menu_btn = QPushButton("\u2261")
        self._menu_btn.setStyleSheet(btn_style)
        self._menu_btn.setToolTip("Menu")
        self._menu_btn.clicked.connect(self._show_menu)
        nav_layout.addWidget(self._menu_btn)

        layout.addWidget(nav)

        # Bookmark bar
        self._bookmark_bar = QWidget()
        self._bookmark_bar.setStyleSheet(f"background: rgb({Theme.BookmarkBar.red()},{Theme.BookmarkBar.green()},{Theme.BookmarkBar.blue()}); padding: 2px 8px;")
        self._bm_layout = QHBoxLayout(self._bookmark_bar)
        self._bm_layout.setContentsMargins(0, 0, 0, 0)
        self._bm_layout.setSpacing(4)
        layout.addWidget(self._bookmark_bar)

        # Find bar (#6) — hidden by default
        self._find_bar = QWidget()
        self._find_bar.setStyleSheet(
            f"background: rgb({Theme.Toolbar.red()},{Theme.Toolbar.green()},{Theme.Toolbar.blue()}); padding: 2px 8px;")
        find_layout = QHBoxLayout(self._find_bar)
        find_layout.setContentsMargins(8, 2, 8, 2)
        find_layout.setSpacing(4)
        find_label = QLabel("Find:")
        find_label.setStyleSheet("color: white; font-size: 12px;")
        find_layout.addWidget(find_label)
        self._find_input = QLineEdit()
        self._find_input.setStyleSheet(
            f"QLineEdit {{ background: rgb({Theme.AddressBox.red()},{Theme.AddressBox.green()},{Theme.AddressBox.blue()});"
            f"color: white; border: 1px solid rgb({Theme.Border.red()},{Theme.Border.green()},{Theme.Border.blue()});"
            f"border-radius: 4px; padding: 2px 8px; font-size: 12px; }}")
        self._find_input.setPlaceholderText("Search in page...")
        self._find_input.returnPressed.connect(self._find_next)
        self._find_input.textChanged.connect(self._find_live)
        find_layout.addWidget(self._find_input, 1)
        find_btn_style = (f"QPushButton {{ background: transparent; color: white; border: none; padding: 2px 6px; font-size: 12px; }}"
                          f"QPushButton:hover {{ background: rgb({Theme.TabHover.red()},{Theme.TabHover.green()},{Theme.TabHover.blue()}); border-radius: 3px; }}")
        prev_btn = QPushButton("\u25b2")
        prev_btn.setStyleSheet(find_btn_style)
        prev_btn.setToolTip("Previous")
        prev_btn.clicked.connect(self._find_prev)
        find_layout.addWidget(prev_btn)
        next_btn = QPushButton("\u25bc")
        next_btn.setStyleSheet(find_btn_style)
        next_btn.setToolTip("Next")
        next_btn.clicked.connect(self._find_next)
        find_layout.addWidget(next_btn)
        close_find_btn = QPushButton("\u2715")
        close_find_btn.setStyleSheet(find_btn_style)
        close_find_btn.setToolTip("Close find bar")
        close_find_btn.clicked.connect(self._close_find_bar)
        find_layout.addWidget(close_find_btn)
        self._find_bar.setVisible(False)
        layout.addWidget(self._find_bar)

        # Web view container
        self._web_panel = QStackedWidget()
        self._web_panel.setStyleSheet(f"background: rgb({Theme.TitleBar.red()},{Theme.TitleBar.green()},{Theme.TitleBar.blue()});")
        layout.addWidget(self._web_panel, 1)

        # Status bar
        self._status_label = QLabel()
        self._status_label.setStyleSheet(
            f"QLabel {{ background: rgb({Theme.StatusBar.red()},{Theme.StatusBar.green()},{Theme.StatusBar.blue()});"
            f"color: rgb({Theme.ForeDim.red()},{Theme.ForeDim.green()},{Theme.ForeDim.blue()}); padding: 2px 8px; font-size: 11px; }}"
        )
        layout.addWidget(self._status_label)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(lambda: self._add_new_tab(self._home_url))
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self._close_current_tab)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._address.setFocus)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._toggle_bookmark)
        QShortcut(QKeySequence("Ctrl+I"), self).activated.connect(self._open_devtools)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._toggle_find_bar)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._close_find_bar)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self).activated.connect(self._restore_closed_tab)
        # Zoom shortcuts (#7)
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self._zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self._zoom_reset)
        # Tab cycling (#21)
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(self._next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(self._prev_tab)

    def _apply_dark_titlebar(self):
        try:
            from ctypes import windll
            HWND = int(self.winId())
            windll.dwmapi.DwmSetWindowAttribute(HWND, 20, int(True), 4)
        except Exception:
            pass

    def _load_initial_settings(self):
        settings = _load_settings()
        self._home_url = settings.get("homepage", self._home_url)
        self._search_template = settings.get("searchurl", self._search_template)

    # === Find-in-page (#6) ===
    def _toggle_find_bar(self):
        visible = not self._find_bar.isVisible()
        self._find_bar.setVisible(visible)
        if visible:
            self._find_input.setFocus()
            self._find_input.selectAll()
        else:
            self._clear_find()

    def _close_find_bar(self):
        self._find_bar.setVisible(False)
        self._clear_find()

    def _find_live(self, text: str):
        tab = self._active_tab()
        if tab and tab.web_view and tab.web_view.page():
            if text:
                tab.web_view.page().findText(text)
            else:
                tab.web_view.page().findText("")

    def _find_next(self):
        text = self._find_input.text()
        tab = self._active_tab()
        if tab and tab.web_view and tab.web_view.page() and text:
            tab.web_view.page().findText(text)

    def _find_prev(self):
        text = self._find_input.text()
        tab = self._active_tab()
        if tab and tab.web_view and tab.web_view.page() and text:
            tab.web_view.page().findText(text, QWebEnginePage.FindFlag.FindBackward)

    def _clear_find(self):
        tab = self._active_tab()
        if tab and tab.web_view and tab.web_view.page():
            tab.web_view.page().findText("")

    # === Zoom controls (#7) ===
    def _zoom_in(self):
        tab = self._active_tab()
        if tab and tab.web_view:
            tab.zoom_factor = min(5.0, tab.zoom_factor + 0.1)
            tab.web_view.setZoomFactor(tab.zoom_factor)
            self._update_zoom_status()

    def _zoom_out(self):
        tab = self._active_tab()
        if tab and tab.web_view:
            tab.zoom_factor = max(0.25, tab.zoom_factor - 0.1)
            tab.web_view.setZoomFactor(tab.zoom_factor)
            self._update_zoom_status()

    def _zoom_reset(self):
        tab = self._active_tab()
        if tab and tab.web_view:
            tab.zoom_factor = 1.0
            tab.web_view.setZoomFactor(1.0)
            self._update_zoom_status()

    def _update_zoom_status(self):
        tab = self._active_tab()
        if tab and abs(tab.zoom_factor - 1.0) > 0.01:
            pct = int(tab.zoom_factor * 100)
            self._status_label.setText(f"Zoom: {pct}%  |  Ads blocked: {self._ad_blocker.blocked_count} | Domains: {len(BLOCKED_AD_DOMAINS)}")
        else:
            self._update_ad_block_status()

    # === Tab cycling (#21) ===
    def _next_tab(self):
        if len(self._tabs) < 2:
            return
        idx = (self._tab_strip.selected_index + 1) % len(self._tabs)
        self._tab_strip.set_current_index(idx)
        self._on_tab_clicked(idx)

    def _prev_tab(self):
        if len(self._tabs) < 2:
            return
        idx = (self._tab_strip.selected_index - 1) % len(self._tabs)
        self._tab_strip.set_current_index(idx)
        self._on_tab_clicked(idx)

    # === Tab restore (#8) ===
    def _restore_closed_tab(self):
        if self._closed_tabs:
            url = self._closed_tabs.pop()
            self._add_new_tab(url)

    # === Ad block status in status bar (#22) ===
    def _update_ad_block_status(self):
        self._status_label.setText(
            f"Ads blocked: {self._ad_blocker.blocked_count} | Domains: {len(BLOCKED_AD_DOMAINS)}")

    # === Autocomplete (#11) ===
    def _update_completer_data(self):
        urls = list(self._history)
        urls.extend(_collect_bookmark_urls(self._bookmarks))
        seen = set()
        unique = []
        for u in urls:
            if u.lower() not in seen:
                seen.add(u.lower())
                unique.append(u)
        from PyQt6.QtCore import QStringListModel
        model = QStringListModel(unique, self._completer)
        self._completer.setModel(model)

    def _add_new_tab(self, url: str = "", insert_after: int = None):
        tab = ChromeTab()
        tab.url = url or self._home_url

        # Use custom BrowserPage for OAuth handling
        tab.web_view = QWebEngineView()
        page = BrowserPage(self._profile, tab.web_view, browser_window=self)
        tab.web_view.setPage(page)

        # Connect signals
        page.loadStarted.connect(lambda: self._on_load_started(tab))
        page.loadFinished.connect(lambda ok: self._on_load_finished(tab, ok))
        page.loadProgress.connect(lambda p: self._on_load_progress(tab, p))
        page.urlChanged.connect(lambda u: self._on_url_changed(tab, u))
        page.titleChanged.connect(lambda t: self._on_title_changed(tab, t))

        # Inject ad hider on load
        page.loadFinished.connect(lambda ok: self._inject_ad_hider(page) if ok else None)

        # Insert tab
        insert_idx = insert_after + 1 if insert_after is not None else len(self._tabs)
        if insert_after is not None and 0 <= insert_after < len(self._tabs):
            self._tabs.insert(insert_idx, tab)
        else:
            self._tabs.append(tab)
            insert_idx = len(self._tabs) - 1

        self._web_panel.addWidget(tab.web_view)
        self._tab_strip.insert_tab(insert_idx, tab, "Loading...")
        self._tab_strip.set_current_index(insert_idx)
        self._active_tab_index = insert_idx
        self._web_panel.setCurrentWidget(tab.web_view)

        # Navigate
        tab.web_view.load(QUrl(tab.url))

    def _on_tab_clicked(self, index: int):
        if 0 <= index < len(self._tabs):
            self._active_tab_index = index
            self._web_panel.setCurrentWidget(self._tabs[index].web_view)
            self._address.setText(self._tabs[index].url)
            self._update_bookmark_star()
            self._update_window_title()
            # Apply per-tab zoom
            tab = self._tabs[index]
            if tab.web_view:
                tab.web_view.setZoomFactor(tab.zoom_factor)
            self._update_zoom_status()

    def _on_tab_close_clicked(self, index: int):
        self._close_tab(index)

    def _safe_close_tab(self, tab):
        """Close a tab by reference, not index (fix #3)."""
        if tab in self._tabs:
            idx = self._tabs.index(tab)
            self._close_tab(idx)

    def _close_tab(self, index: int):
        if len(self._tabs) <= 1:
            return
        tab = self._tabs.pop(index)
        # Save URL for restore (#8)
        if tab.url and tab.url != "about:blank":
            self._closed_tabs.append(tab.url)
            if len(self._closed_tabs) > 20:
                self._closed_tabs = self._closed_tabs[-20:]
        self._web_panel.removeWidget(tab.web_view)
        tab.web_view.deleteLater()
        self._tab_strip.remove_tab(index)

        if self._active_tab_index >= len(self._tabs):
            self._active_tab_index = len(self._tabs) - 1
        if 0 <= self._active_tab_index < len(self._tabs):
            self._tab_strip.set_current_index(self._active_tab_index)
            self._web_panel.setCurrentWidget(self._tabs[self._active_tab_index].web_view)
            self._update_window_title()

    def _close_current_tab(self):
        self._close_tab(self._tab_strip.selected_index)

    def _on_load_started(self, tab: ChromeTab):
        tab.is_loading = True
        tab.load_progress = 0
        self._tab_strip.update()
        if tab == self._active_tab():
            self._status_label.setText("Loading...")

    def _on_load_finished(self, tab: ChromeTab, ok: bool):
        tab.is_loading = False
        tab.load_progress = 100
        idx = self._tabs.index(tab) if tab in self._tabs else -1
        if idx >= 0:
            self._tab_strip.set_tab_text(idx, tab.title[:25] if tab.title else "New Tab")
        self._update_ad_block_status()
        self._add_to_history(tab.url)
        self._try_autofill(tab)

        # Auto-close auth callback tabs (like Ceprkac)
        self._check_auto_close_auth_tab(tab)

    def _on_load_progress(self, tab: ChromeTab, progress: int):
        tab.load_progress = progress
        idx = self._tabs.index(tab) if tab in self._tabs else -1
        if idx >= 0 and tab.is_loading:
            self._tab_strip.set_tab_text(idx, f"Loading {progress}%")
        self._tab_strip.update()

    def _on_url_changed(self, tab: ChromeTab, url: QUrl):
        tab.url = url.toString()
        if tab == self._active_tab():
            self._address.setText(tab.url)
        # Re-trigger autofill for multi-step logins
        self._try_autofill(tab)

    def _on_title_changed(self, tab: ChromeTab, title: str):
        tab.title = title
        idx = self._tabs.index(tab) if tab in self._tabs else -1
        if idx >= 0:
            self._tab_strip.set_tab_text(idx, title[:25] if title else "New Tab")
        # Update window title (#20)
        if tab == self._active_tab():
            self._update_window_title()

    def _update_window_title(self):
        """Set window title to '{tab title} - GBrowser' (#20)."""
        tab = self._active_tab()
        if tab and tab.title:
            self.setWindowTitle(f"{tab.title} - GBrowser")
        else:
            self.setWindowTitle("GBrowser")

    def _active_tab(self) -> ChromeTab | None:
        if 0 <= self._active_tab_index < len(self._tabs):
            return self._tabs[self._active_tab_index]
        return None

    def _on_ad_blocked_navigation(self, page):
        """Handle ad-blocked navigation like Ceprkac - go back or close tab."""
        tab = self._find_tab_by_page(page)
        if not tab:
            return
        # Use tab reference, not captured index (fix #3)
        is_empty = not tab.url or tab.url == "about:blank" or tab.url.startswith("data:")
        if is_empty and len(self._tabs) > 1:
            QTimer.singleShot(100, lambda: self._safe_close_tab(tab))
        else:
            # Tab has content - go back
            tab.web_view.back()

    def _find_tab_by_page(self, page) -> ChromeTab | None:
        for tab in self._tabs:
            if tab.web_view and tab.web_view.page() == page:
                return tab
        return None

    def _handle_new_window_url(self, page, url: QUrl):
        """Handle new window creation (OAuth popups)."""
        url_str = url.toString()
        if _is_ad_url(url_str):
            return  # Block ad popups
        # For auth flows, open in new tab
        if _is_auth_url(url_str):
            self._add_new_tab(url_str)
        else:
            # Regular links open in new tab
            self._add_new_tab(url_str)

    def _check_auto_close_auth_tab(self, tab: ChromeTab):
        """Auto-close auth callback tabs like Ceprkac."""
        url = tab.url.lower()
        if "/callback" in url and ("oauth" in url or "auth" in url):
            # Auth callback - auto-close after delay, using tab reference (fix #3)
            QTimer.singleShot(1500, lambda: self._safe_close_tab(tab))

    def _on_download_requested(self, download):
        """Handle download requests like Ceprkac's DownloadStarting."""
        suggested_path = download.suggestedFileName()
        path, _ = QFileDialog.getSaveFileName(self, "Save As", suggested_path)
        if path:
            download.setDownloadFileName(path)
            download.accept()
            # Track download (#12)
            dl_item = DownloadItem(suggested_path)
            self._downloads.append(dl_item)
            if len(self._downloads) > 20:
                self._downloads = self._downloads[-20:]
            self._status_label.setText(f"Downloading: {suggested_path}")
            download.downloadProgress.connect(
                lambda received, total: self._update_download_status(received, total, dl_item))
            download.finished.connect(lambda: self._download_finished(dl_item))
        else:
            download.cancel()

    def _update_download_status(self, received: int, total: int, dl_item: DownloadItem):
        dl_item.received = received
        dl_item.total = total
        if total > 0:
            self._status_label.setText(f"Downloading {dl_item.filename}: {received}/{total} bytes")
        else:
            self._status_label.setText(f"Downloading {dl_item.filename}: {received} bytes")

    def _download_finished(self, dl_item: DownloadItem):
        dl_item.status = "Complete"
        self._status_label.setText(f"Download complete: {dl_item.filename}")

    def _show_downloads(self):
        """Show download manager dialog (#12)."""
        dlg = DownloadManagerDialog(self._downloads, self)
        dlg.exec()

    def _inject_ad_hider(self, page):
        """Inject ad blocking scripts — matches Ceprkac's InjectAdElementHider + InjectMainWorldBlocker."""
        try:
            url = page.url().toString()
            page_host = urlparse(url).hostname or ""
            page_host = page_host.lower()
        except Exception:
            page_host = ""

        # YouTube gets its own dedicated ad blocking
        is_youtube = page_host in ("www.youtube.com", "youtube.com", "m.youtube.com", "music.youtube.com") \
            or page_host.endswith(".youtube.com") or page_host.endswith(".youtube-nocookie.com")

        if is_youtube:
            page.runJavaScript(YOUTUBE_AD_BLOCKER_JS)
            # Also inject main-world YouTube blocker via <script> tag
            page.runJavaScript(YOUTUBE_MAIN_WORLD_INJECTOR_JS)
            return

        # Skip generic element hiding on whitelisted sites (non-YouTube)
        if _is_whitelisted(page_host):
            return

        page.runJavaScript(AD_ELEMENT_HIDER_JS)

        # Use cached main-world blocker JS (perf improvement #14)
        if self._cached_main_world_js:
            page.runJavaScript(self._cached_main_world_js)

    def _try_autofill(self, tab: ChromeTab):
        now = time.time()
        if now - tab.last_autofill_attempt < 3:
            return
        tab.last_autofill_attempt = now

        if not self._passwords.passwords:
            return

        try:
            domain = urlparse(tab.url).hostname
            if not domain:
                return
            domain = domain.lower()
        except Exception:
            return

        matches = self._passwords.get_matches(domain)
        if not matches:
            return

        path_lower = urlparse(tab.url).path.lower() + (urlparse(tab.url).query or "").lower()
        is_login_page = any(kw in path_lower for kw in
                            ["login", "signin", "sign-in", "auth", "account", "sso",
                             "register", "signup", "sign-up"])

        self._autofill_attempt(tab, matches, is_login_page, 0, domain)

    def _autofill_attempt(self, tab: ChromeTab, matches: list[SavedCredential],
                          is_login_page: bool, attempt: int, domain: str):
        if attempt >= 6:
            return
        delay = 800 + attempt * 600

        def do_check():
            # Tab-alive guard (fix #4)
            if tab not in self._tabs or tab.web_view is None:
                return
            if not tab.web_view.page():
                return
            tab.web_view.page().runJavaScript(CHECK_LOGIN_FIELDS_JS, 0,
                lambda result: self._handle_field_check(tab, matches, is_login_page, attempt, domain, result))

        QTimer.singleShot(delay, do_check)

    def _handle_field_check(self, tab: ChromeTab, matches: list[SavedCredential],
                            is_login_page: bool, attempt: int, domain: str, result):
        if not result:
            return
        # Tab-alive guard (fix #4)
        if tab not in self._tabs or tab.web_view is None:
            return
        field_status = result.strip('"') if isinstance(result, str) else str(result)

        if field_status == "none":
            self._autofill_attempt(tab, matches, is_login_page, attempt + 1, domain)
            return

        if field_status == "useronly" and not is_login_page:
            return

        if field_status in ("both", "pwonly"):
            if len(matches) == 1:
                js = _make_fill_js(matches[0].username, matches[0].password)
                tab.web_view.page().runJavaScript(js)
                self._status_label.setText(f"Auto-filled credentials for {domain}")
            else:
                self._show_credential_picker(tab, matches)
            return

        if field_status == "useronly":
            if len(matches) == 1:
                js = _make_fill_username_js(matches[0].username)
                tab.web_view.page().runJavaScript(js)
                self._status_label.setText(f"Filled username for {domain}")
            else:
                self._show_credential_picker(tab, matches)

    def _show_credential_picker(self, tab: ChromeTab, matches: list[SavedCredential]):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background: rgb({Theme.ActiveTab.red()},{Theme.ActiveTab.green()},{Theme.ActiveTab.blue()});"
            f"color: white; }} QMenu::item:selected {{ background: rgb({Theme.TabHover.red()},{Theme.TabHover.green()},{Theme.TabHover.blue()}); }}")
        header = menu.addAction("Select account:")
        header.setEnabled(False)
        menu.addSeparator()
        for cred in matches:
            action = menu.addAction(cred.username)
            action.triggered.connect(lambda checked, c=cred: self._fill_selected_credential(tab, c))
        menu.exec(self._web_panel.mapToGlobal(QPoint(self._web_panel.width() // 2 - 80, 10)))

    def _fill_selected_credential(self, tab: ChromeTab, cred: SavedCredential):
        if tab.web_view and tab.web_view.page():
            js = _make_fill_js(cred.username, cred.password)
            tab.web_view.page().runJavaScript(js)
            self._status_label.setText(f"Filled credentials for {cred.username}")

    def _toggle_bookmark(self):
        tab = self._active_tab()
        if not tab:
            return
        url = tab.url
        if not url:
            return
        if _remove_bookmark(self._bookmarks, url):
            _save_bookmarks(self._bookmarks)
            self._refresh_bookmarks_bar()
            self._bookmark_btn.setText("\u2606")
            self._status_label.setText("Bookmark removed.")
        else:
            self._bookmarks.insert(0, BookmarkNode("link", tab.title or _display_title(url), url))
            _save_bookmarks(self._bookmarks)
            self._refresh_bookmarks_bar()
            self._bookmark_btn.setText("\u2605")
            self._status_label.setText("Bookmark added.")
        self._update_completer_data()

    def _bookmark_hash(self) -> int:
        """Compute a simple hash of bookmark list for incremental update check (#15)."""
        h = len(self._bookmarks)
        for n in self._bookmarks:
            h = h * 31 + hash(n.title) + hash(getattr(n, 'href', ''))
        return h

    def _refresh_bookmarks_bar(self):
        # Incremental update: skip rebuild if bookmarks haven't changed (#15)
        new_hash = self._bookmark_hash()
        if new_hash == self._last_bookmark_hash:
            return
        self._last_bookmark_hash = new_hash

        while self._bm_layout.count():
            item = self._bm_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        bm_btn_style = (f"QPushButton {{ background: rgb({Theme.AddressBox.red()},{Theme.AddressBox.green()},{Theme.AddressBox.blue()});"
                        f"color: white; border: none; border-radius: 4px; padding: 2px 8px; font-size: 11px; }}"
                        f"QPushButton:hover {{ background: rgb({Theme.TabHover.red()},{Theme.TabHover.green()},{Theme.TabHover.blue()}); }}")

        # Calculate how many bookmarks fit before overflow (#10)
        max_bar_width = max(200, self.width() - 80)
        used_width = 0
        visible_count = 0
        avg_btn_width = 100  # approximate width per bookmark button

        for node in self._bookmarks:
            est_width = min(len(node.title), 30) * 7 + 20  # rough estimate
            if used_width + est_width > max_bar_width and visible_count > 0:
                break
            used_width += est_width
            visible_count += 1

        for i, node in enumerate(self._bookmarks[:visible_count]):
            if node.type == "folder":
                btn = QPushButton(node.title[:30])
                btn.setStyleSheet(bm_btn_style)
                menu = QMenu(btn)
                menu.setStyleSheet(
                    f"QMenu {{ background: rgb({Theme.ActiveTab.red()},{Theme.ActiveTab.green()},{Theme.ActiveTab.blue()});"
                    f"color: white; }} QMenu::item:selected {{ background: rgb({Theme.TabHover.red()},{Theme.TabHover.green()},{Theme.TabHover.blue()}); }}")
                self._add_children_to_menu(menu, node.children)
                btn.setMenu(menu)
                self._bm_layout.addWidget(btn)
            else:
                btn = QPushButton(node.title[:30])
                btn.setStyleSheet(bm_btn_style)
                href = node.href
                btn.clicked.connect(lambda checked, u=href: self._navigate_tab(self._active_tab(), u) if self._active_tab() else None)
                self._bm_layout.addWidget(btn)

        # Overflow button (>>) if there are more bookmarks (#10)
        if visible_count < len(self._bookmarks):
            overflow_btn = QPushButton("\u00bb")
            overflow_btn.setStyleSheet(bm_btn_style)
            overflow_btn.setToolTip("More bookmarks")
            overflow_menu = QMenu(overflow_btn)
            overflow_menu.setStyleSheet(
                f"QMenu {{ background: rgb({Theme.ActiveTab.red()},{Theme.ActiveTab.green()},{Theme.ActiveTab.blue()});"
                f"color: white; }} QMenu::item:selected {{ background: rgb({Theme.TabHover.red()},{Theme.TabHover.green()},{Theme.TabHover.blue()}); }}")
            for node in self._bookmarks[visible_count:]:
                if node.type == "folder":
                    sub = overflow_menu.addMenu(node.title[:40])
                    sub.setStyleSheet(overflow_menu.styleSheet())
                    self._add_children_to_menu(sub, node.children)
                else:
                    href = node.href
                    action = overflow_menu.addAction(node.title[:40])
                    action.triggered.connect(lambda checked, u=href: self._navigate_tab(self._active_tab(), u) if self._active_tab() else None)
            overflow_btn.setMenu(overflow_menu)
            self._bm_layout.addWidget(overflow_btn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._bm_layout.addWidget(spacer)

    def _add_children_to_menu(self, menu: QMenu, children: list[BookmarkNode]):
        for child in children:
            if child.type == "folder":
                sub = menu.addMenu(child.title)
                sub.setStyleSheet(menu.styleSheet())
                self._add_children_to_menu(sub, child.children)
            else:
                href = child.href
                action = menu.addAction(child.title)
                action.triggered.connect(lambda checked, u=href: self._navigate_tab(self._active_tab(), u) if self._active_tab() else None)

    def _import_bookmarks_html(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Bookmarks", "",
                                              "Bookmark Files (*.html *.htm);;All Files (*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                html_text = f.read()
            parsed = _parse_bookmarks_html(html_text)
            self._bookmarks.clear()
            self._bookmarks.extend(parsed)
            _save_bookmarks(self._bookmarks)
            self._last_bookmark_hash = 0  # Force rebuild
            self._refresh_bookmarks_bar()
            self._update_completer_data()
            count = _count_links(self._bookmarks)
            self._status_label.setText(f"Imported {count} bookmarks.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Import failed:\n{e}")

    def _export_bookmarks_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Bookmarks", "bookmarks.html",
                                              "Bookmark File (*.html)")
        if not path:
            return
        try:
            _export_bookmarks_html(self._bookmarks, path)
            count = _count_links(self._bookmarks)
            self._status_label.setText(f"Exported {count} bookmarks.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed:\n{e}")

    def _clear_bookmarks(self):
        reply = QMessageBox.question(self, "Confirm", "Clear all bookmarks?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._bookmarks.clear()
            _save_bookmarks(self._bookmarks)
            self._last_bookmark_hash = 0
            self._refresh_bookmarks_bar()
            self._update_completer_data()
            self._status_label.setText("Bookmarks cleared.")

    def _add_to_history(self, url: str):
        if not url:
            return
        self._history = [h for h in self._history if h.lower() != url.lower()]
        self._history.append(url)
        if len(self._history) > 100:
            self._history = self._history[-100:]
        _save_history(self._history)
        self._update_completer_data()

    def _clear_history(self):
        reply = QMessageBox.question(self, "Confirm", "Clear all history?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._history.clear()
            _save_history(self._history)
            self._update_completer_data()
            self._status_label.setText("History cleared.")

    def _show_history_dialog(self):
        """Show history dialog (#9)."""
        dlg = HistoryDialog(self._history, self)
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted:
            url = dlg.selected_url()
            if url:
                tab = self._active_tab()
                if tab:
                    self._navigate_tab(tab, url)
                else:
                    self._add_new_tab(url)
        elif result == 2:  # Clear
            self._history.clear()
            _save_history(self._history)
            self._update_completer_data()
            self._status_label.setText("History cleared.")

    def _import_passwords_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Passwords (Chrome/Edge CSV)",
                                              "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        try:
            count = self._passwords.import_csv(path)
            self._status_label.setText(f"Imported {count} passwords.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Import failed:\n{e}")

    def _clear_passwords(self):
        reply = QMessageBox.question(self, "Confirm", "Clear all saved passwords?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._passwords.clear()
            self._status_label.setText("Passwords cleared.")

    def _show_search_engine_picker(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Choose Your Search Engine")
        dlg.setFixedSize(360, 340)
        dlg.setStyleSheet(
            f"QDialog {{ background: rgb({Theme.ActiveTab.red()},{Theme.ActiveTab.green()},{Theme.ActiveTab.blue()}); color: white; }}")

        layout = QVBoxLayout(dlg)
        label = QLabel("Select your default search engine:")
        label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(label)

        listbox = QListWidget()
        listbox.setStyleSheet(
            f"QListWidget {{ background: rgb({Theme.TitleBar.red()},{Theme.TitleBar.green()},{Theme.TitleBar.blue()});"
            f"color: white; border: 1px solid rgb({Theme.Border.red()},{Theme.Border.green()},{Theme.Border.blue()}); }}"
            f"QListWidget::item:selected {{ background: rgb({Theme.Accent.red()},{Theme.Accent.green()},{Theme.Accent.blue()}); color: black; }}")
        listbox.setFont(QFont("Segoe UI", 11))
        for name, _, _ in SEARCH_ENGINES:
            listbox.addItem(name)
        listbox.setCurrentRow(0)
        layout.addWidget(listbox)

        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet(
            f"QPushButton {{ background: rgb({Theme.Accent.red()},{Theme.Accent.green()},{Theme.Accent.blue()});"
            f"color: black; border: none; border-radius: 4px; padding: 8px 24px; font-size: 13px; }}")
        ok_btn.clicked.connect(dlg.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignRight)

        dlg.exec()
        if listbox.currentRow() >= 0:
            idx = listbox.currentRow()
            _, home, search = SEARCH_ENGINES[idx]
            self._home_url = home
            self._search_template = search
            _save_settings(self._home_url, self._search_template)

    def _show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background: rgb({Theme.ActiveTab.red()},{Theme.ActiveTab.green()},{Theme.ActiveTab.blue()});"
            f"color: white; }} QMenu::item:selected {{ background: rgb({Theme.TabHover.red()},{Theme.TabHover.green()},{Theme.TabHover.blue()}); }}"
            f"QMenu::separator {{ background: rgb({Theme.Border.red()},{Theme.Border.green()},{Theme.Border.blue()}); height: 1px; }}")

        menu.addAction("New Tab (Ctrl+T)", lambda: self._add_new_tab(self._home_url))
        menu.addAction("Restore Closed Tab (Ctrl+Shift+T)", self._restore_closed_tab)
        menu.addSeparator()
        menu.addAction("Find in Page (Ctrl+F)", self._toggle_find_bar)
        menu.addSeparator()
        menu.addAction("Add Bookmark (Ctrl+D)", self._toggle_bookmark)
        menu.addAction("Import Bookmarks...", self._import_bookmarks_html)
        menu.addAction("Export Bookmarks...", self._export_bookmarks_html)
        menu.addAction("Clear Bookmarks", self._clear_bookmarks)
        menu.addSeparator()
        menu.addAction("View History...", self._show_history_dialog)
        menu.addAction("Clear History", self._clear_history)
        menu.addSeparator()
        menu.addAction("Downloads...", self._show_downloads)
        menu.addSeparator()
        menu.addAction("Import Passwords (CSV)...", self._import_passwords_csv)
        menu.addAction("Clear Saved Passwords", self._clear_passwords)
        menu.addSeparator()
        menu.addAction("DevTools (Ctrl+I)", self._open_devtools)
        menu.addAction("Change Search Engine...", self._show_search_engine_picker)
        menu.addSeparator()
        menu.addAction("Exit", self.close)

        menu.exec(self._menu_btn.mapToGlobal(QPoint(0, self._menu_btn.height())))

    def _open_devtools(self):
        tab = self._active_tab()
        if tab and tab.web_view and tab.web_view.page():
            inspector = QWebEngineView()
            tab.web_view.page().setDevToolsPage(inspector.page())
            inspector.setWindowTitle("DevTools")
            inspector.resize(900, 600)
            inspector.show()
            if not hasattr(self, '_devtools_windows'):
                self._devtools_windows = []
            self._devtools_windows.append(inspector)

    def _on_address_enter(self):
        text = self._address.text().strip()
        if not text:
            return
        url = text
        if not text.startswith(("http://", "https://", "file://")):
            if "." in text and " " not in text:
                url = "https://" + text
            else:
                url = self._search_template.format(quote_plus(text))
        tab = self._active_tab()
        if tab and tab.web_view:
            tab.url = url
            tab.web_view.load(QUrl(url))

    def _go_back(self):
        tab = self._active_tab()
        if tab and tab.web_view:
            tab.web_view.back()

    def _go_forward(self):
        tab = self._active_tab()
        if tab and tab.web_view:
            tab.web_view.forward()

    def _reload(self):
        tab = self._active_tab()
        if tab and tab.web_view:
            tab.web_view.reload()

    def _navigate_tab(self, tab: ChromeTab | None, url: str):
        if tab and tab.web_view:
            tab.url = url
            tab.web_view.load(QUrl(url))

    def _update_bookmark_star(self):
        tab = self._active_tab()
        if tab and tab.url and _bookmark_exists(self._bookmarks, tab.url):
            self._bookmark_btn.setText("\u2605")
        else:
            self._bookmark_btn.setText("\u2606")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Debounced bookmark bar overflow recalculation on resize
        if not hasattr(self, '_resize_timer'):
            self._resize_timer = QTimer(self)
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._on_resize_done)
        self._resize_timer.start(150)

    def _on_resize_done(self):
        self._last_bookmark_hash = 0
        self._refresh_bookmarks_bar()

    def closeEvent(self, event):
        try:
            g = self.geometry()
            cfg = {
                "geometry": {
                    "x": g.x(), "y": g.y(),
                    "width": g.width(), "height": g.height(),
                    "maximized": self.isMaximized()
                }
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass
        super().closeEvent(event)


def _resource_path(filename: str) -> str:
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        path = os.path.join(base, filename)
        if os.path.exists(path):
            return path
        path = os.path.join(os.path.dirname(sys.executable), filename)
        if os.path.exists(path):
            return path
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


if __name__ == "__main__":
    # Fix QtWebEngine GPU/sandbox issues in virtualized environments
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu --no-sandbox --disable-software-rasterizer")

    # Ensure exceptions aren't silently swallowed by Qt
    def _excepthook(exc_type, exc_value, exc_tb):
        import traceback
        traceback.print_exception(exc_type, exc_value, exc_tb)
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    sys.excepthook = _excepthook

    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("Gorstak.GBrowser.5.4")
    except Exception:
        pass

    app = QApplication(sys.argv)

    ico_path = _resource_path("GBrowser.ico")
    if os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        geo = cfg.get("geometry", {})
    except Exception:
        geo = {}

    try:
        win = Browser()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nFATAL: Browser failed to initialize: {e}", file=sys.stderr)
        sys.exit(1)

    if geo:
        if geo.get("maximized"):
            win.showMaximized()
        else:
            win.setGeometry(geo.get("x", 100), geo.get("y", 100),
                            geo.get("width", 1280), geo.get("height", 860))
            win.show()
    else:
        win.resize(1280, 860)
        win.show()

    sys.exit(app.exec())

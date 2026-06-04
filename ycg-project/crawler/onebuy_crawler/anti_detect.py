"""Playwright 浏览器反检测工具 — 供所有爬虫脚本复用.

针对 JD/淘宝的增强反检测: Canvas指纹、AudioContext指纹、WebGL指纹、
navigator属性全覆盖、chrome对象模拟、权限API、Battery API等.
"""

from __future__ import annotations

import random
from pathlib import Path

ANTI_DETECTION_INIT_SCRIPT = """
(function() {
    'use strict';

    // ========== 1. navigator 属性全覆盖 ==========
    const overwriteProp = (obj, key, getter) => {
        try { Object.defineProperty(obj, key, { get: getter, configurable: true }); } catch(e) {}
    };

    overwriteProp(navigator, 'webdriver', () => false);
    overwriteProp(navigator, 'vendor', () => 'Google Inc.');
    overwriteProp(navigator, 'vendorSub', () => '');
    overwriteProp(navigator, 'productSub', () => '20030107');
    overwriteProp(navigator, 'platform', () => 'Win32');
    overwriteProp(navigator, 'maxTouchPoints', () => 0);
    overwriteProp(navigator, 'hardwareConcurrency', () => 8);
    overwriteProp(navigator, 'deviceMemory', () => 8);
    overwriteProp(navigator, 'languages', () => ['zh-CN', 'zh', 'en-US', 'en']);
    overwriteProp(navigator, 'language', () => 'zh-CN');
    overwriteProp(navigator, 'appVersion', () =>
        '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    );
    overwriteProp(navigator, 'userAgent', () =>
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    );
    overwriteProp(navigator, 'userAgentData', () => ({
        brands: [
            {brand: 'Google Chrome', version: '131'},
            {brand: 'Chromium', version: '131'},
            {brand: 'Not_A Brand', version: '24'}
        ],
        mobile: false,
        platform: 'Windows'
    }));
    overwriteProp(navigator, 'connection', () => ({
        effectiveType: '4g',
        rtt: 50,
        downlink: 10,
        saveData: false
    }));

    // ========== 2. plugins & mimeTypes ==========
    overwriteProp(navigator, 'plugins', () => {
        const PluginArrayProto = Object.create(PluginArray.prototype);
        const plugins = [
            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1},
            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '', length: 1},
            {name: 'Native Client', filename: 'internal-nacl-plugin', description: '', length: 2}
        ];
        const arr = Object.setPrototypeOf(plugins, PluginArrayProto);
        arr.item = (i) => arr[i] || null;
        arr.namedItem = (name) => arr.find(p => p.name === name) || null;
        arr.refresh = () => {};
        return arr;
    });

    overwriteProp(navigator, 'mimeTypes', () => {
        const MimeTypeArrayProto = Object.create(MimeTypeArray.prototype);
        const types = [
            {type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format'},
            {type: 'text/pdf', suffixes: 'pdf', description: 'Portable Document Format'}
        ];
        const arr = Object.setPrototypeOf(types, MimeTypeArrayProto);
        arr.item = (i) => arr[i] || null;
        arr.namedItem = (name) => arr.find(t => t.type === name) || null;
        return arr;
    });

    // ========== 3. chrome 对象模拟 ==========
    if (!window.chrome) {
        window.chrome = {
            runtime: {
                OnInstalledReason: { INSTALL: 'install', UPDATE: 'update', CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update' },
                OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
                RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' },
                connect: function() {},
                getManifest: function() { return { version: '1.0', name: 'Chrome', manifest_version: 2 }; },
                getURL: function(path) { return 'chrome-extension://mockid/' + path; },
                id: undefined,
                onConnect: { addListener: function() {} },
                onMessage: { addListener: function() {} },
                sendMessage: function() {}
            },
            loadTimes: function() {
                return {
                    requestTime: Date.now() / 1000,
                    startLoadTime: Date.now() / 1000,
                    commitLoadTime: Date.now() / 1000,
                    finishDocumentLoadTime: Date.now() / 1000,
                    finishLoadTime: Date.now() / 1000,
                    firstPaintTime: Date.now() / 1000,
                    firstPaintAfterLoadTime: 0,
                    navigationType: 'Other',
                    wasFetchedViaSpdy: false,
                    wasNpnNegotiated: false,
                    npnNegotiatedProtocol: 'unknown',
                    wasAlternateProtocolAvailable: false,
                    connectionInfo: 'http/1.1'
                };
            },
            csi: function() {
                return {
                    startE: Date.now(),
                    onloadT: Date.now(),
                    pageT: (Math.random() * 300 + 100),
                    tran: 15
                };
            },
            app: {}
        };
    }

    // ========== 4. 权限查询 ==========
    if (window.navigator.permissions) {
        const origQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
        window.navigator.permissions.query = function(parameters) {
            if (parameters.name === 'notifications') {
                return Promise.resolve({ state: 'prompt', onchange: null });
            }
            return origQuery(parameters).then(result => result, () => ({ state: 'prompt', onchange: null }));
        };
    }

    // ========== 5. WebGL 指纹混淆 ==========
    const origWebGLGetParam = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) return 'Intel Inc.';
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) return 'Intel(R) UHD Graphics 630';
        // MAX_TEXTURE_SIZE
        if (parameter === 3379) return 16384;
        return origWebGLGetParam.call(this, parameter);
    };

    if (typeof WebGL2RenderingContext !== 'undefined') {
        const origWebGL2GetParam = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel(R) UHD Graphics 630';
            if (parameter === 3379) return 16384;
            return origWebGL2GetParam.call(this, parameter);
        };
    }

    // ========== 6. Canvas 指纹混淆 ==========
    const fpNoise = () => Math.random() * 0.1 - 0.05;

    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {
        const ctx = this.getContext('2d');
        if (ctx) {
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] = Math.min(255, Math.max(0, imageData.data[i] + Math.round(fpNoise())));
                imageData.data[i+1] = Math.min(255, Math.max(0, imageData.data[i+1] + Math.round(fpNoise())));
                imageData.data[i+2] = Math.min(255, Math.max(0, imageData.data[i+2] + Math.round(fpNoise())));
            }
            ctx.putImageData(imageData, 0, 0);
        }
        return origToDataURL.apply(this, arguments);
    };

    // ========== 7. AudioContext 指纹混淆 ==========
    if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {
        const AC = window.AudioContext || window.webkitAudioContext;
        const origCreateOscillator = AC.prototype.createOscillator;
        AC.prototype.createOscillator = function() {
            const osc = origCreateOscillator.call(this);
            const origGetPeriodicWave = osc.getPeriodicWave || function(){};
            return osc;
        };

        const origGetChannelData = AudioBuffer.prototype.getChannelData;
        AudioBuffer.prototype.getChannelData = function(channel) {
            const data = origGetChannelData.call(this, channel);
            for (let i = 0; i < Math.min(data.length, 10); i++) {
                data[i] += fpNoise();
            }
            return data;
        };
    }

    // ========== 8. Battery API ==========
    if (navigator.getBattery) {
        const origGetBattery = navigator.getBattery.bind(navigator);
        navigator.getBattery = function() {
            return origGetBattery().then(function(battery) {
                overwriteProp(battery, 'charging', () => true);
                overwriteProp(battery, 'level', () => 0.98 + Math.random() * 0.02);
                return battery;
            });
        };
    }

    // ========== 9. 屏蔽自动化检测属性 ==========
    delete window.__nightmare;
    delete window.__playwright__binding__;
    delete window.__selenium_unwrapped;
    delete window.__webdriver_evaluate;
    delete window.__webdriver_script_function;
    delete window.__webdriver_script_func;
    delete window.__webdriver_script_fn;
    delete window.__fxdriver_evaluate;
    delete window.__driver_unwrapped;
    delete window.__webdriver_unwrapped;
    delete window.__webdriver_script_fn;
    delete window.__webdriver_script_func;
    delete window.__webdriver_script_function;
    delete document.__webdriver_evaluate;
    delete document.__selenium_evaluate;
    delete document.__webdriver_script_function;
    delete document.__webdriver_script_func;
    delete document.__webdriver_script_fn;
    delete document.__fxdriver_evaluate;
    delete document.__driver_unwrapped;
    delete document.__webdriver_unwrapped;

    // ========== 10. 媒体设备枚举 ==========
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        const origEnumerate = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
        navigator.mediaDevices.enumerateDevices = function() {
            return origEnumerate().then(function(devices) {
                return devices.filter(function(d) {
                    return d.kind !== 'audiooutput' || d.deviceId !== 'default';
                });
            });
        };
    }

    console.debug = function() {};
})();
"""

COMMON_BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-infobars",
    "--disable-dev-shm-usage",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-web-security",
    "--disable-features=BlockInsecurePrivateNetworkRequests",
    "--disable-features=TranslateUI",
    "--disable-ipc-flooding-protection",
    "--disable-gpu-sandbox",
    "--disable-software-rasterizer",
    "--disable-sync",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-component-update",
    "--disable-background-networking",
    "--mute-audio",
    "--no-default-browser-check",
    "--no-first-run",
    "--password-store=basic",
    "--use-mock-keychain",
]

BROWSER_PROFILE_DIR = Path("browser_profiles")

VIEWPORT_SIZES = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1920, "height": 1080},
    {"width": 1600, "height": 900},
]

EXTRA_HTTP_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def apply_stealth_to_page(page) -> None:
    try:
        from playwright_stealth import Stealth
        Stealth().apply_stealth_sync(page)
    except ImportError:
        pass
    except Exception:
        pass
    page.add_init_script(ANTI_DETECTION_INIT_SCRIPT)
    try:
        page.set_extra_http_headers(EXTRA_HTTP_HEADERS)
    except Exception:
        pass


def get_stealth_context_args(headless: bool, proxy_url: str = "") -> dict:
    viewport = random.choice(VIEWPORT_SIZES)

    kwargs: dict = {
        "headless": headless,
        "viewport": viewport,
        "locale": "zh-CN",
        "timezone_id": "Asia/Shanghai",
        "args": list(COMMON_BROWSER_ARGS),
        "ignore_https_errors": True,
    }

    if not headless:
        kwargs["viewport"] = None

    if proxy_url:
        kwargs["proxy"] = {"server": proxy_url}

    return kwargs
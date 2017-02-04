var eve_image;
(function createProxFunc() {
	var webpProxySupport = (waitlist.base.getMetaData("eve-image-server-webp") === "True");
	var webpBrowserSupport = (waitlist.base.getMetaData("browser-webp") === "True");
	var proxyUrl = waitlist.base.getMetaData("eve-image-server");

	console.log("Proxy Supports WebP: ", webpProxySupport);
	console.log("Browser Supports WebP:", webpBrowserSupport);

	eve_image = function(path, suffix) {
		if (webpProxySupport && webpBrowserSupport) {
			suffix = "webp";
		}
		return proxyUrl.replace("${ path }", path).replace("${ suffix }", suffix);
	}
})();
var i18nloaded = $.i18n({
	locale: '{{ lang_code }}'
}).load({
	"{{ lang_code }}": {% assets "i18n." + lang_code %}"{{ ASSET_URL }}"{% endassets %}
});
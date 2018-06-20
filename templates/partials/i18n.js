var i18nloaded = $.i18n({
	locale: '{{ lang_code }}'
}).load({
	en: {% assets "i18n.en" %}'{{ ASSET_URL }}'{% endassets %},
	de: {% assets "i18n.de" %}'{{ ASSET_URL }}'{% endassets %},
});
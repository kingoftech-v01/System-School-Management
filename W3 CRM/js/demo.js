"use strict"

var themeOptionArr = {
	typography: '',
	version: '',
	layout: '',
	primary: '',
	headerBg: '',
	navheaderBg: '',
	sidebarBg: '',
	sidebarStyle: '',
	sidebarPosition: '',
	headerPosition: '',
	containerLayout: '',
};


(function($) {
	
	"use strict"
	
	var theme =  getUrlParams('theme');
	
	/* Dz Theme Demo Settings  */
	var dzThemeSet0 = {
		/* Default Theme */
		typography: "poppins",
		version: "light",
		layout: "vertical",
		primary: "color_1",
		headerBg: "color_4",
		navheaderBg: "color_4",
		sidebarBg: "color_1",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	var dzThemeSet1 = {
		typography: "poppins",
		version: "light",
		layout: "vertical",
		primary: "color_1",
		headerBg: "color_1",
		navheaderBg: "color_4",
		sidebarBg: "color_4",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	var dzThemeSet2 = {
		typography: "poppins",
		version: "light",
		layout: "horizontal",
		primary: "color_2",
		headerBg: "color_2",
		navheaderBg: "color_2",
		sidebarBg: "color_1",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	var dzThemeSet3 = {
		typography: "poppins",
		version: "light",
		layout: "vertical",
		primary: "color_8",
		headerBg: "color_1",
		navheaderBg: "color_8",
		sidebarBg: "color_1",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	var dzThemeSet4 = {
		typography: "poppins",
		version: "light",
		layout: "vertical",
		primary: "color_5",
		headerBg: "color_5",
		navheaderBg: "color_5",
		sidebarBg: "color_1",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	var dzThemeSet5 = {
		typography: "poppins",
		version: "light",
		layout: "vertical",
		primary: "color_11",
		headerBg: "color_1",
		navheaderBg: "color_11",
		sidebarBg: "color_11",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	var dzThemeSet6 = {
		typography: "poppins",
		version: "light",
		layout: "vertical",
		primary: "color_5",
		headerBg: "color_1",
		navheaderBg: "color_1",
		sidebarBg: "color_1",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	var dzThemeSet7 = {
		typography: "poppins",
		version: "light",
		layout: "vertical",
		primary: "color_9",
		headerBg: "color_1",
		navheaderBg: "color_9",
		sidebarBg: "color_9",
		sidebarStyle: "full",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	var dzThemeSet8 = {
		typography: "poppins",
		version: "light",
		layout: "vertical",
		primary: "color_10",
		headerBg: "color_1",
		navheaderBg: "color_10",
		sidebarBg: "color_10",
		sidebarStyle: "mini",
		sidebarPosition: "fixed",
		headerPosition: "fixed",
		containerLayout: "full",
	};
	
	function themeChange(theme){
		var themeSettings = {};
		themeSettings = eval('dzThemeSet'+theme);
		dzSettingsOptions = themeSettings; /* For Screen Resize */
		new dzSettings(themeSettings);
		
		setThemeInCookie(themeSettings);
	}
	
	function setThemeInCookie(themeSettings){
		jQuery.each(themeSettings, function(optionKey, optionValue) {
			setCookie(optionKey,optionValue);
		});
	}
	
	function setThemeLogo() {
		var logo = getCookie('logo_src');
		
		var logo2 = getCookie('logo_src2');
		
		if(logo != ''){
			jQuery('.nav-header .logo-abbr').attr("src", logo);
		}
		
		if(logo2 != ''){
			jQuery('.nav-header .logo-compact, .nav-header .brand-title').attr("src", logo2);
		}
	}
	
	function setThemeOptionOnPage(){
		if(getCookie('version') != ''){
			jQuery.each(themeOptionArr, function(optionKey, optionValue) {
				var optionData = getCookie(optionKey);
				themeOptionArr[optionKey] = (optionData != '')?optionData:dzSettingsOptions[optionKey];
			});
			
			dzSettingsOptions = themeOptionArr;
			new dzSettings(dzSettingsOptions);
			
			setThemeLogo();
		}
	}
	
	jQuery(document).on('click', '.dz_theme_demo', function(){
		var demoTheme = jQuery(this).data('theme');
		themeChange(demoTheme, 'ltr');
		
	});
	
	jQuery(document).on('click', '.dz_theme_demo_rtl', function(){
		var demoTheme = jQuery(this).data('theme');
		themeChange(demoTheme, 'rtl');
	});
	
	//jQuery(window).on('load', function(){
	//	if(theme != undefined){
	//		themeChange(theme);
	//	}else if(getCookie('version') == ''){	
	//		themeChange(0);
	//	}
	//	
	//	setThemeOptionOnPage();
	//	
	//});
	
	jQuery(window).on('resize', function(){
		setThemeOptionOnPage();
	});
	

})(jQuery);
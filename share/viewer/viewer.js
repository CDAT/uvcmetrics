$("body").ready(function(){
	$("a[href$='.png']").popover({
		"content": function(){
			var link = $(this);
			var img_url = link.attr("href");
			var img = document.createElement("img");
			$(img).attr('src', img_url).attr('width', "100%");
			return img;
		},
		"trigger": "hover",
		"placement": "left",
		"html": true
	});
});
function setSelectedThumbnail(thumb, key) {
	/* update class for previously selected item */
	clearSelectedThumbnail();

	/* update class for currently selected item and update the input */
	thumb.classList.add("active");
	document.getElementById("thumb-select").value = key;

	/* remove any file that had been selected for upload */
	document.getElementById("thumb-upload").value = "";
}

function clearSelectedThumbnail() {
	var thumbs = document.getElementsByClassName("img-thumbnail-select");

	for ( var i = 0; i < thumbs.length; ++i ) {
		thumbs[i].classList.remove("active");
	}
}

function deleteArticle(article_id) {
	var request = new XMLHttpRequest();
	request.open("DELETE", "/article/" + article_id + "/edit", true);

	request.onload = function() {
		if ( request.status == 200 ) {
			document.location.replace("/");
		} else {
			/* TODO: do something useful if we get an error */	
		}
	}

	request.send();
}

function deleteSponsor(sponsor_id) {
	var request = new XMLHttpRequest();
	request.open("DELETE", "/sponsors/" + sponsor_id + "/edit", true);

	request.onload = function() {
		if ( request.status == 200 ) {
			document.location.reload();
		} else {
			/* TODO: do something useful if we get an error */
		}
	}

	request.send();
}

function hhh(i) {
    
    $.getJSON('/currentdfratios/' + i[0],function(data) {
	console.log(data);
	$("#ratios > tbody").empty();
	$("#ratiodate").html('<b>Date:</b> ' + data['Date']);
	$.each(data['Ratios'], function(key1,value1) {
	    $.each(value1, function(index,value2) {
		console.log("index " + index + " value2: " + value2);
		$('#ratios > tbody:last-child').append('<tr><td>' + index + '</td><td>' + value2[1] + '</td></tr>');
	    });
	});
    });
    
}

function get_plot(choice) {
    if(choice.length != 0) {
	$.post('/getplot', {'choice' : choice}, function(response){
	    $('#butthole').empty().append(response);
	});
    }
    else {
	alert('Please provide input!');
    }
}

function current_df_name(chosen_tick,choice) {
    $.getJSON('/currentdfname', function(data) {
	current_tick = data['df_name'];
	if(current_tick != chosen_tick) {
	    if (confirm('Gave me different ticker than before,\ndo you want to load a new Ticker?')) {
		window.location = "/datadisplay";
	    } 
	}
    });

    //return false; // temporary
}

function start_long_task(tick) {
    // add task status elements

    var div = $('<div id="progress"><div></div><div>0%</div><div>...</div><div>&nbsp;</div></div><hr>');
    $('#progress').append(div); //must be hashtag id string

    // create a progress bar
    var nanobar = new Nanobar({ bg: '#44f', target: div[0].childNodes[0] });
    
    // send ajax POST request to start background job
    // ajax is asynchronus
    $.ajax({
	type: 'POST',
	url:  '/getdataframe/' + tick,
	success: function(data, status, request) {
	    status_url = request.getResponseHeader('Location');
	    update_progress(status_url, nanobar, div[0]);
	},
	error: function() {
	    alert('Unexpected error');
	}
    });
    return false; //hot tip this makes sure form action doesn't return to /datadisplay
}
function update_progress(status_url, nanobar, status_div) {
    // send GET request to status URL
    $.getJSON(status_url, function(data) {
	//update UI
	percent = parseInt(data['percent']);
	if (data['state'] != 'PENDING' && data['state'] != 'PROGRESS') {
	    if ('result' in data) {
		//show result
		$(status_div.childNodes[2]).text('Done');
		$(status_div.childNodes[3]).text('Result: ' + data['result']);

		// is this ghetto I copy from stack exchange, to redirect fillout a
		// (hidden?) form then submit it so that we load datadisplay in POST
		// then we play with dataframe
		var url = '/datadisplay';
		var form = $('<form action="' + url + '" method="post">' +
			     '<input type="hidden" name="api_url" value="nothing" />' +
			     '</input>');
		$('body').append(form);
		form.submit();
	    }
	    else {
		// something bad happened
		$(status_div.childNodes[3]).text('Result: ' + data['state']);
	    }
	}
	else {
	    // rerun in 1.0 seconds
	    nanobar.go(percent);
	    $(status_div.childNodes[1]).text(percent + '%');
	    $(status_div.childNodes[2]).text(data['state'] + ' : ' + data['message']);

	    setTimeout(function() {
		update_progress(status_url, nanobar, status_div);
	    }, 1000);
	}
    });
}

$(document).ready(function() {
    $('#fuck').click(function() {
	current_df_name($('#baka').val(),$('#doji').val());
	get_plot($('#doji').val());
    });
    
    $('#boke').click(function() {
	if(!$('#baka').val()) { window.alert("You must supply S&P ticker"); }
	else { this.disabled = true;
	       start_long_task($('#baka').val()); }
    });

});



/*@cc_on
$.each(['article', 'aside', 'canvas', 'details', 'figcaption', 'figure', 'footer', 'header',
'hgroup', 'menu', 'nav', 'section', 'summary'], function() { document.createElement(this); });
@*/

var toggle_animating = function() {}

function load_canvas() {
	var is_timer_on = false;
	var canvas = $('<canvas width="960" height="36" onclick="toggle_animating()"></canvas>');
	var e = canvas.get(0);
	if (!e.getContext) return;
	canvas.appendTo('hgroup');
	var c = e.getContext('2d');

	if ($('body').hasClass('ver-copious')) {
		var grad = c.createLinearGradient(0, e.height * 2 / 3, 0, e.height);
		grad.addColorStop(0, '#223');
		grad.addColorStop(1, '#fff');
		c.fillStyle = grad;
		c.fillRect(0, 0, e.width, e.height);

		var points = [];
		c.fillStyle = 'white';
		c.lineWidth = 0.5;
		c.strokeStyle = 'white';
		for (var i = 0; i < 200; ++i) {
			var x, y, dx, dy, dist;
			var keepgoing = true;
			while (keepgoing) {
				x = Math.random() * e.width;
				y = 2 + e.height * (1 - Math.pow(Math.random(), 6));
				keepgoing = false;
				for (var j = 0; j < i; ++j) {
					dx = x - points[j][0];
					dy = y - points[j][1];
					if (dx * dx + dy * dy < 30) {
						keepgoing = true;
						break;
					}
				}
			}
			for (var j = 0; j < i; ++j) {
				dx = x - points[j][0];
				dy = y - points[j][1];
				dist = dx * dx + dy * dy;
				if (dist < 2000 && dist > 300 && Math.random() < 0.03) {
					c.beginPath();
					c.moveTo(x, y);
					c.lineTo(points[j][0], points[j][1]);
					c.stroke();
				}
			}
			points.push([x, y]);
			c.beginPath();
			c.arc(x, y, y / 20 + 1, 0, 360, false);
			c.fill();
		}
	} else { // knit
		var waves = [
		/*[	p: position,
			s: speed,
			b: bold,
			f: frequency,
			a: amplitude ]
			[  p,   s,   b,   f,   a] */
			[1.3,-4.4, 2.0, 2.0, 1.0],
			[2.0,-2.2, 1.0, 2.0, 1.0],
			[0.8,+2.2, 1.0, 2.0, 1.0],
			[2.8,-2.2, 0.5, 1.0, 0.5]
		];	
		var fps= 15;
		var  n = 15;			// number of samples
		var wh = e.height - 2;	// wave height
		var cw = e.width;		// canvas width
		var ch = e.height;		// canvas height
		var bh = (ch - wh) / 2;
		var draw = function(is_final) {
			var nn = n;
			if (is_final) { nn = 200; }
			c.fillStyle = 'white';
			c.clearRect(0, 0, e.width, e.height);
			c.strokeStyle = 'black';

			{
				c.beginPath();
				c.moveTo(0,wh/2+bh);
				for (var j = 0; j <= nn; ++j) {
					var pos = j/nn;
					v = wh;
					for (var i = 1, wave; wave = waves[i]; ++i) {
						var nv = wh/2 + Math.sin(wave[3]*pos*3.14+wave[0]) * wh/2 * wave[4];
						if (nv < v) v = nv;
					}
					c.lineTo(j*cw/nn, v+bh);
				}
				c.lineTo(cw, ch+bh);
				c.lineTo(0, ch+bh);
				c.closePath();
				c.fill();
			}

			for (var i = 0, wave; wave = waves[i]; ++i) {
				var wp = wave[0], ws = wave[1], wb = wave[2], wf = wave[3], wa = wave[4];
				c.lineWidth = wave[2];
				c.beginPath();
				c.moveTo(0, wh/2 + Math.sin(wave[0]) * wh/2 * wave[4] + bh);
				for (var j = 1; j <= nn; j++) {
					var pos = 1.0*j/nn;
					var v = wh/2 + Math.sin(wave[3]*pos*3.14+wave[0]) * wh/2 * wave[4];
					c.lineTo(j*cw/nn, v+bh);
				}
				c.stroke();
				wave[0] += wave[1]/fps;
			}
			if (is_timer_on)
				setTimeout(function(){draw(false);}, 1000/fps);
			else if (!is_final)
				setTimeout(function(){draw(true);}, 1000/fps);
		};
		draw(true);
		is_timer_on = true;
		setTimeout(function(){draw(false)}, 3000);
		toggle_animating = function() {
			if (is_timer_on = !is_timer_on) { draw(false); }
		}
	}
}

/*
// experimental. may be suspended without notice.
function load_jubegraph_update(label, username) {
	var waiting = '읽는 중입니다...';
	document.write('<button id="jubegraph-update">' + label + '</button>');
	var button = $('#jubegraph-update');
	var rollback = function() {
		alert('데이터를 읽는 도중 문제가 발생했습니다. 나중에 다시 시도해 주세요.');
		button.removeAttr('disabled').text(label);
	};
	button.click(function() {
		var u = encodeURIComponent(username);
		button.attr('disabled', 'disabled').text(waiting);
		$.ajax({async:true, url:'/knit/'+u+'/massda/main', dataType:'text', success:function(main) {
			$.ajax({async:true, url:'/knit/'+u+'/massda/score', dataType:'text', success:function(score) {
				var form = $('<form method="post" target="_new" ' +
					'action="http://jubegraph.dyndns.org/jubeat_knit/cgi/registFile.cgi">' +
					'<input type="hidden" name="playerData"/><input type="hidden" name="musicData"/>' +
					'<input type="submit" name="submit" value="データ登録"/></form>');
				form.find('[name=playerData]').val(main);
				form.find('[name=musicData]').val(score);
				$('body').append(form);
				//form.get(0).submit();
				//$('body').remove(form);
				button.text('성공!'); // do not enable the button -- intended
			}, error:rollback});
		}, error:rollback});
		return false;
	});
}
*/

function select_user() {
	if ($('h1').hasClass('selecting-user')) {
		return true;
	} else {
		$('h1').addClass('selecting-user');
		$('h1 input:text').focus();
		return false;
	}
}

function build_xfmt(fmt) {
	return function(v) {
		var m;
		w = (v * fmt.mult).toFixed(fmt.digits);
		while ((m = w.match(/^-?\d{4,}/))) {
			w = w.substring(0, m[0].length-3) + ',' + w.substring(m[0].length-3);
		}
		switch (fmt.sign) {
		case 1: w = (v>=0 ? '+' : '').w; break;
		case 2: w = (v>0 ? '+' : (v==0 ? '±' : '')).w; break;
		}
		return fmt.prefix + w + fmt.suffix;
	};
}

function graph_init(gather, section_id, options) {
$(function() {
	var width = 700, height = 480, hmargin = 10, vmargin = 10;
	var section_key = '#'+section_id;
	var left = $(section_key+' .graph-left'), right = $(section_key+' .graph-right'), dataset = $(section_key+' .graph-dataset');
	var fmt = dataset.data('fmt');
	var paper = Raphael(left.get(0), width, height);
	options = options || {};
	var data = gather(dataset);
	//window.data = data;

	// NaN-removing Math.min/max alternatives
	var minnum = function(x,y) { return (isNaN(x) ? y : isNaN(y) ? x : Math.min(x,y)); }
	var maxnum = function(x,y) { return (isNaN(x) ? y : isNaN(y) ? x : Math.max(x,y)); }

	var x = data[0].x, y = data[0].y, y2 = data[0].y2;
	var minx = x, miny = minnum(y,y2), maxx = x, maxy = maxnum(y,y2);
	var highlighted = null;
	for (var i = 1; i < data.length; ++i) {
		x = data[i].x; y = data[i].y; y2 = data[i].y2;
		minx = Math.min(x, minx); miny = Math.min(minnum(y,y2), miny);
		maxx = Math.max(x, maxx); maxy = Math.max(maxnum(y,y2), maxy);
		if (data[i].highlight) highlighted = i;
	}
	
	// try to adjust the lone circle to the center of the graph.
	var smallx = 1, smally = Math.pow(10, -fmt.digits);
	if (maxx - minx < smallx) {
		maxx += smallx;
		minx -= smallx;
	}
	if (maxy - miny < smally) {
		maxy += smally;
		miny -= smally;
	}

	var drawhtick = function(y, title) {
		paper.path(['M', 0, y, 'H', width]).attr({stroke: '#ccc', 'stroke-width': 1});
		if (title) {
			paper.text(5, y-6, title).attr({font: '12px Arial', fill: '#444', 'text-anchor': 'start'});
		}
	};
	var drawticks = function(low, high, size) {
		// this algorithm is in large part originated from flot.
		var nticks = 0.3 * Math.sqrt(size);
		var delta = (high - low) / nticks * fmt.mult;
		var deltaexpt = Math.floor(Math.log(delta) / Math.LN10);
		var deltamagn = Math.pow(10, deltaexpt);
		var deltanorm = delta / deltamagn; // [1.0,10.0)
		if (deltanorm < 1.5) {
			deltanorm = 1;
		} else if (deltanorm < 2.25) {
			deltanorm = 2;
		} else if (deltanorm < 3) {
			deltanorm = 2.5;
			--deltaexpt;
		} else if (deltanorm < 7.5) {
			deltanorm = 5;
		} else {
			deltanorm = 10;
		}
		delta = deltanorm * deltamagn / fmt.mult;
		var path = [];
		var extradigits = Math.max(0, -deltaexpt);
		fmt.digits = extradigits;
		var xfmt = build_xfmt(fmt);

		var start = delta * Math.floor(low / delta);
		var offset = 10, mult = size / (high - low);
		if (fmt.flip) {
			offset += size;
			mult = -mult;
		}
		var prev = Number.NaN, v = Number.NaN, y;
		var i = 0;
		do {
			prev = v;
			v = start + i++ * delta;
			y = offset + (high - v) * mult;
			drawhtick(y, xfmt(v));
		} while (prev != v && v < high);
	};
	var drawpoint = function(coord, color) {
		return paper.circle(coord[0], coord[1], 3).attr({fill: '#fff', stroke: color || '#000', 'stroke-width': 2});
	};
	var drawplot = function(coords, color) {
		var path = [], cur = null, prev;
		for (var i = 0; i < coords.length; ++i) {
			cur = coords[i];
			if (i == 0) {
				path.push('M', cur[0], cur[1]);
				prev = cur;
			} else if (Math.abs(cur[0] - prev[0]) + Math.abs(cur[1] - prev[1]) > 0.5) {
				// coarser drawing for TBS
				path.push('L', cur[0], cur[1]);
				prev = cur;
			}
		}
		if (path.length) {
			paper.path(path).attr({stroke: color || '#000', 'stroke-width': 2});
		}
	};

	var points = [], points2 = [], indices = [], indices2 = [];
	var xmult = (width - 2*hmargin) / (maxx - minx);
	var yoffset = hmargin, ymult = (height - 2*hmargin) / (maxy - miny);
	if (fmt.flip) {
		yoffset += height - 2*vmargin;
		ymult = -ymult;
	}
	for (var i = 0; i < data.length; ++i) {
		var x = hmargin + (data[i].x - minx) * xmult;
		var y = yoffset + (maxy - data[i].y) * ymult;
		var y2 = yoffset + (maxy - data[i].y2) * ymult;
		if (!isNaN(data[i].y)) {
			indices.push(i);
			points.push([x, y]);
		}
		if (!isNaN(data[i].y2)) {
			indices2.push(i);
			points2.push([x, y2]);
		}
	}

	drawticks(miny, maxy, height - 2*vmargin);
	drawplot(points);
	drawplot(points2, '#888');
	if (!options.nopoints) {
		$.each(points, function(i) {
			data[indices[i]].point = drawpoint(this);
		});
		$.each(points2, function(i) {
			data[indices2[i]].point2 = drawpoint(this, '#888');
		});
	}

	var vline = paper.path('M0,0').attr({stroke: '#f00', 'stroke-width': 0.5});
	var scrollto = function(x) {
		if (data.length == 0) return; // no use

		// find the nearest point via binary search
		var low = 0, high = data.length - 1;
		var mirrored = (data[low].x > data[high].x);
		while (high >= low) {
			var mid = (low + high) >> 1;
			var xdiff = data[mid].x - x;
			if (mirrored) xdiff = -xdiff;
			if (xdiff > 0) {
				high = mid - 1;
			} else if (xdiff < 0) {
				low = mid + 1;
			} else {
				low = high = mid;
				break;
			}
		}

		var nearest;
		if (high < 0) {
			nearest = low;
		} else if (low >= data.length) {
			nearest = high;
		} else {
			nearest = (Math.abs(x - data[low].x) < Math.abs(x - data[high].x) ? low : high);
		}

		var node = data[nearest].node;
		right.get(0).scrollTop = node.offsetTop - (height - node.offsetHeight) / 2;
		if (highlighted !== null) {
			data[highlighted].node.className = '';
			if (data[highlighted].point) data[highlighted].point.attr('stroke', '#000');
			if (data[highlighted].point2) data[highlighted].point2.attr('stroke', '#888');
		}
		node.className = 'highlight';
		if (data[nearest].point) data[nearest].point.attr('stroke', '#f00');
		if (data[nearest].point2) data[nearest].point2.attr('stroke', '#ff8080');
		highlighted = nearest;
	};
	
	if (highlighted) {
		var x = data[highlighted].x;
		var linex = (x - minx) * xmult + hmargin;
		vline.attr('path', ['M', linex, 0, 'V', height]);
		scrollto(x);
	}

	left.bind('selectstart', function() { return false; });
	left.mousedown(function(e) {
		var onmousemove = function(e) {
			var x = e.clientX - left.offset().left;
			if (x < hmargin) x = hmargin;
			if (x > width - hmargin) x = width - hmargin;
			vline.attr('path', ['M', x, 0, 'V', height]);
			scrollto((x - hmargin) / xmult + minx);
		};
		var onmouseup = function() {
			left.unbind('mousemove', onmousemove);
			$('body').unbind('mouseup', onmouseup);
		};
		left.bind('mousemove', onmousemove);
		onmousemove(e);
		$('body').bind('mouseup', onmouseup);
	});
});
}

function get_history(dataset) {
	return dataset.find('tbody tr').map(function() {
		var v = this.getAttribute('data-v'), v2 = this.getAttribute('data-v2');
		var highlight = this.getAttribute('class') == 'highlight';
		return {node: this,
			x: Number(this.getAttribute('data-k')),
			y: (v === null ? Math.NaN : Number(v)),
			y2: (v2 === null ? Math.NaN : Number(v2)),
			highlight: highlight};
	}).get();
}

function get_rank(dataset) {
	var rank = 0;
	return dataset.find('tbody tr').map(function() {
		var v = this.getAttribute('data-v');
		var highlight = this.getAttribute('class') == 'highlight';
		return {node: this,
			x: ++rank,
			y: (v === null ? Math.NaN : Number(v)),
			highlight: highlight};
	}).get();
}


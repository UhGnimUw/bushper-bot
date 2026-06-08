$(".divscroll").scrollTop('500');
$(document).ready(function() {
	//定义svg变量将布局svg1选出来
	var svg = d3.select("#svg1"), 
		width = svg.attr("width"), 
		height = svg.attr("height");
	//定义name变量制作图标
	//城市名,英文名,别名,人口数量,地区生产总值,车牌号,行政级别,省份
	var names = ['行政级别', '城市名', '省份'];
	var colors = ['#6ca46c', '#4e88af', '#ca635f'];	
	
	//背景颜色设置 补充CSS样式设置字体布局
	for (var i=0; i < names.length; i++) {
		$('#indicator').append("<div><span style='background-color:" + colors[i] + "'></span>" + names[i] + "</div>");
	}
	
	//利用d3.forceSimulation()定义关系图 包括设置边link、排斥电荷charge、关系图中心点
	var simulation = d3.forceSimulation()
			.force("link", d3.forceLink().id(d => {
				// console.log(d)
				return d.id
			}))
			.force("charge", d3.forceManyBody())
			.force("center", d3.forceCenter(width / 2, height / 2))
			.force("collision", d3.forceCollide(30)) 
	
	var graph
	let nodes =[]
	let links = []	 
	let nodeSet = [] 
	
	$.ajax({
		url:"http://localhost:5000/json",
		async:false,
		success:function(result){
			showData(JSON.parse(result))
		},
		error:function(){
			alert('后端错误，请重试！')
		}
	});

	function showData(data){
		graph = data
		console.log(graph[0].p)
		for (let item of graph) {
			if(nodeSet.indexOf(item.p.start.identity) == -1){
				nodeSet.push(item.p.start.identity)
				nodes.push({
					id: item.p.start.identity,
					label: item.p.start.labels[0],
					properties: item.p.start.properties
				})
			}
			if(nodeSet.indexOf(item.p.end.identity) == -1){
				nodeSet.push(item.p.end.identity)
				nodes.push({
					id: item.p.end.identity,
					label: item.p.end.labels[0],
					properties: item.p.end.properties
				})
			}
			links.push({
				source: item.p.segments[0].relationship.start,
				target: item.p.segments[0].relationship.end,
				type: item.p.segments[0].relationship.type,
				properties: item.p.segments[0].relationship.properties
			})
		}

		var link = svg.append("g").attr("class","links").selectAll("line").data(links).enter()
		.append("line").attr("stroke-width", function(d) {
			return 1.2
		});
		
		var node = svg.append("g").attr("class", "nodes").selectAll("circle").data(nodes).enter()
		.append("circle").attr("r", function(d) {
			let size = 15
			switch(d.label){
				case '行政级别': size = 16;break;
				case '城市': size = 14; break;
				case '省份': size = 12;break;
				default: size=14;break;
			}
			return size
		}).attr("fill", function(d) {
			let index = 0
			switch(d.label){
				case '行政级别': index = 0; break;
				case '省份': index = 1;break;
				case '城市': index = 2;break;
				default: index=0;break;
			}
			return colors[index]
		}).attr("stroke", "none").attr("name", function(d) {
			let tmp;
			switch(d.label){
				case '行政级别': tmp = d.properties.level; break;
				case '省份': tmp = d.properties.province;break;
				case '城市': tmp = d.properties.name;break;
				default: tmp=d.properties.name;break;
			}
			return tmp;
		}).attr("id", d => d.id)
		.call(d3.drag()
			.on("start", dragstarted)
			.on("drag", dragged)
			.on("end", dragended)
		);
		
		var text = svg.append("g").attr("class", "texts").selectAll("text").data(nodes).enter()
		.append("text").attr("font-size", function(d) {
				return 13;
			}).attr("fill", function(d) {
					let index = 0
					switch(d.label){
						case '行政级别': inedx = 0; break;
						case '省份': index = 1;break;
						case '城市': index = 2;break;
						default: index=0;break;
					}
					return colors[index];
			}).attr('name', function(d) {
				let tmp;
				switch(d.label){
					case '行政级别': tmp = d.properties.level; break;
					case '省份': tmp = d.properties.province;break;
					case '城市': tmp = d.properties.name;break;
					default: tmp=d.properties.name;break;
				}
				return tmp;
			}).text(function(d) {
				let tmp;
				switch(d.label){
					case '行政级别': tmp = d.properties.level; break;
					case '省份': tmp = d.properties.province;break;
					case '城市': tmp = d.properties.name;break;
					default: tmp=d.properties.name;break;
				}
				return tmp;
			})
				
		node.append("title").text(d => d.properties.nam)
		
		simulation.nodes(nodes).on("tick", ticked);
			
		simulation.force("link")
				.links(links)
				.distance(d => {
					let distance = 10
					switch(d.source.label){
						case '行政级别': distance += 30;break;
						case '省份': distance += 25;break;
						case '城市': distance += 20;break;
						default: distance += 15;break; 
					}
					switch(d.target.label){
						case '行政级别': distance += 30;break;
						case '省份': distance += 25;break;
						case '城市': distance += 20;break;
						default: distance += 15;break; 
					}
					return distance
				});
			
		function ticked() {
				link
						.attr("x1", function(d) {
							return d.source.x;
						})
						.attr("y1", function(d) {
							return d.source.y;
						})
						.attr("x2", function(d) {
							return d.target.x;
						})
						.attr("y2", function(d) {
							return d.target.y;
						});
		
				node
						.attr("cx", function(d) {
								return d.x;
						})
						.attr("cy", function(d) {
								return d.y;
						});
		
				text.attr('transform', function(d) {
					let size = 15
					switch(d.label){
						case '行政级别': break;
						case '省份': size = 14;break;
						case '城市': size = 13;break;
						default: size = 12;break;
					}
					return 'translate(' + (d.x - size / 2) + ',' + (d.y + size / 2) + ')';
				});
		}
	}
	
	var dragging = false;
	function dragstarted(d) {
		if (!d3.event.active) simulation.alphaTarget(0.3).restart();
		d.fx = d.x;
		d.fy = d.y;
	}
	function dragged(d) {
		d.fx = d3.event.x;
		d.fy = d3.event.y;
	}
	function dragended(d) {
		if (!d3.event.active) simulation.alphaTarget(0);
		d.fx = null;
		d.fy = null;
	}
	$('#mode span').click(function(event) {
			$('#mode span').removeClass('active');
			$(this).addClass('active');
			console.log($(this).text())
			if ($(this).text() == '图形') {
					$('.texts text').hide();
					$('.nodes circle').show();
			} else {
					$('.texts text').show();
					$('.nodes circle').hide();
			}
	});
	$('#bnt-search').click(function(event) {
		var text = $('#form-control').val();
		htmlobj=$.ajax({
			url:"http://localhost:5000/answer/" + text,
			async:false,
			success:function(result){
				alert(result)
			},
			error:function(){
				alert('后端错误，请重试！')
			}
		});
	});
	$('#svg1').on('mouseenter', '.nodes circle', function(event) {
		if(!dragging) {
			var name = $(this).attr("name");

			var id = $(this).attr("id");
			$('#info h4').css('color', $(this).attr('fill')).text(name);
			$('#info p').remove();
			for(let item of nodes){
				if(item.id == id){
					for(var key in item.properties)
					$('#info').append('<p><span>' + key + '</span>' + item.properties[key] + '</p>');
				}
			}
			d3.select('#svg1 .nodes').selectAll('circle').attr('class', function(d) {
				let tmp;
				switch(d.label){
					case '行政级别': tmp = d.properties.level; break;
					case '省份': tmp = d.properties.province;break;
					case '城市': tmp = d.properties.name;break;
					default: tmp=d.properties.name;break;
				}
				if(tmp == name) {
					return '';
				} 
				else {
					for (var i = 0; i < links.length; i++) {
						let ts, tt;
						switch(links[i]['source'].label){
							case '行政级别': ts = links[i]['source'].properties.level; break;
							case '省份': ts = links[i]['source'].properties.province;break;
							case '城市': ts = links[i]['source'].properties.name;break;
							default: ts = links[i]['source'].properties.name;break;
						}
						switch(links[i]['target'].label){
							case '行政级别': tt = links[i]['target'].properties.level; break;
							case '省份': tt = links[i]['target'].properties.province;break;
							case '城市': tt = links[i]['target'].properties.name;break;
							default: tt = links[i]['target'].properties.name;break;
						}
						if (ts == name && links[i]['target'].id == d.id) {
								return '';
						}
						if (tt == name && links[i]['source'].id == d.id) {
								return '';
						}
					}
					return "inactive"; 
				}
			});
			d3.select("#svg1 .links").selectAll('line').attr('class', function(d) {
					let ts, tt;
					switch(d.source.label){
						case '行政级别': ts = d.source.properties.level; break;
						case '省份': ts = d.source.properties.province;break;
						case '城市': ts = d.source.properties.name;break;
						default: ts = d.source.properties.name;break;
					}
					switch(d.target.label){
						case '行政级别': tt = d.target.properties.level; break;
						case '省份': tt = d.target.properties.province;break;
						case '城市': tt = d.target.properties.name;break;
						default: tt = d.target.properties.name;break;
					}
					if (ts == name || tt == name) {
							return '';
					} else {
							return 'inactive';
					}
			});
		}
	});
	$('#svg1').on('mouseleave', '.nodes circle', function(event) {
		d3.select('#svg1 .nodes').selectAll('circle').attr('class', '');
		d3.select('#svg1 .links').selectAll('line').attr('class', '');
	});
	$('#svg1').on('mouseenter', '.texts text', function(event) {
		if (!dragging) {
			var name = $(this).attr('name');
	
			$('#info h4').css('color', $(this).attr('fill')).text(name);
			$('#info p').remove();
			for(let item of nodes){
				if(item.properties.name == name){
					for(var key in item.properties)
								$('#info').append('<p><span>' + key + '</span>' + item.properties[key] + '</p>');
				}
			}
	
			d3.select('#svg1 .texts').selectAll('text').attr('class', function(d) {
				let tmp;
				switch(d.label){
					case '行政级别': tmp = d.properties.level; break;
					case '省份': tmp = d.properties.province;break;
					case '城市': tmp = d.properties.name;break;
					default: tmp=d.properties.name;break;
				}						
				if (tmp == name) {
					return '';
				}
	
				for (var i = 0; i < links.length; i++) {
					let ts, tt;
					switch(links[i]['source'].label){
						case '行政级别': ts = links[i]['source'].properties.level; break;
						case '省份': ts = links[i]['source'].properties.province;break;
						case '城市': ts = links[i]['source'].properties.name;break;
						default: ts = links[i]['source'].properties.name;break;
					}
					switch(links[i]['target'].label){
						case '行政级别': tt = links[i]['target'].properties.level; break;
						case '省份': tt = links[i]['target'].properties.province;break;
						case '城市': tt = links[i]['target'].properties.name;break;
						default: tt = links[i]['target'].properties.name;break;
					}
					if (ts == name && links[i]['target'].id == d.id) {
							return '';
					}
					if (tt == name && links[i]['source'].id == d.id) {
							return '';
					}
				}
				return 'inactive';
			});
			d3.select("#svg1 .links").selectAll('line').attr('class', function(d) {
				let ts, tt;
				switch(d.source.label){
					case '行政级别': ts = d.source.properties.level; break;
					case '省份': ts = d.source.properties.province;break;
					case '城市': ts = d.source.properties.name;break;
					default: ts = d.source.properties.name;break;
				}
				switch(d.target.label){
					case '行政级别': tt = d.target.properties.level; break;
					case '省份': tt = d.target.properties.province;break;
					case '城市': tt = d.target.properties.name;break;
					default: tt = d.target.properties.name;break;
				}
				if (ts == name || tt == name) {
						return '';
				} else {
						return 'inactive';
				}
			});
		}
	});
	$('#svg1').on('mouseleave', '.texts text', function(event) {
		if (!dragging) {
			d3.select('#svg1 .texts').selectAll('text').attr('class', '');
			d3.select('#svg1 .links').selectAll('line').attr('class', '');
		}
	});
});
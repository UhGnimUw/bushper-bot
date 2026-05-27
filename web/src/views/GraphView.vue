<template>
  <div class="graph-view">
    <div class="graph-header">
      <h1>中国主要城市信息知识图谱</h1>
    </div>
    <div class="graph-container">
      <div class="graph-main">
        <div class="graph-scroll" ref="scrollEl">
          <svg ref="svgEl" id="svg1"></svg>
        </div>
      </div>
      <div class="sidebar">
        <div class="sidebar-card">
          <h3>图例</h3>
          <div id="indicator">
            <div><span style="background:#6ca46c;"></span>行政级别</div>
            <div><span style="background:#4e88af;"></span>省份</div>
            <div><span style="background:#ca635f;"></span>城市</div>
          </div>
          <div id="mode">
            <span class="active">图形</span>
            <span>文字</span>
          </div>
        </div>
        <div class="sidebar-card">
          <h3>节点信息</h3>
          <div id="info"><h4 style="color:#8a8a8a;font-size:13px;">悬停查看详情</h4></div>
        </div>
        <div class="sidebar-card">
          <h3>问答查询</h3>
          <div class="search-box">
            <input type="text" v-model="queryText" placeholder="如：浙江省有哪些城市、杭州市的人口..." @keydown.enter="doSearch">
            <button @click="doSearch" :disabled="searching">{{ searching ? '...' : '查询' }}</button>
          </div>
          <div v-if="answer" id="answer-result">{{ answer }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as d3 from 'd3'

const svgEl = ref(null)
const scrollEl = ref(null)
const queryText = ref('')
const answer = ref('')
const searching = ref(false)

let simulation = null
let graph = null
let nodes = []
let links = []
let nodeSet = []

const colors = ['#6ca46c', '#4e88af', '#ca635f']

onMounted(async () => {
  await nextTick()
  if (svgEl.value) {
    await loadGraphData()
  }
})

async function loadGraphData() {
  try {
    const res = await fetch('/api/graph/data')
    const data = await res.json()
    if (data.ok) {
      showData(data.data)
    }
  } catch (e) {
    console.error('Failed to load graph data:', e)
  }
}

function showData(data) {
  graph = data
  const svg = d3.select(svgEl.value)
  const container = scrollEl.value
  const width = Math.max(1400, container?.clientWidth || 1400)
  const height = Math.max(800, container?.clientHeight || 800)
  svg.attr('width', width).attr('height', height)

  simulation = d3.forceSimulation()
    .force('link', d3.forceLink().id(d => d.id))
    .force('charge', d3.forceManyBody())
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide(30))

  for (const item of graph) {
    if (nodeSet.indexOf(item.p.start.identity) === -1) {
      nodeSet.push(item.p.start.identity)
      nodes.push({
        id: item.p.start.identity,
        label: item.p.start.labels[0],
        properties: item.p.start.properties
      })
    }
    if (nodeSet.indexOf(item.p.end.identity) === -1) {
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
      type: item.p.segments[0].relationship.type
    })
  }

  const link = svg.append('g').attr('class', 'links')
    .selectAll('line').data(links).enter()
    .append('line').attr('stroke-width', 1.2)

  const node = svg.append('g').attr('class', 'nodes')
    .selectAll('circle').data(nodes).enter()
    .append('circle')
    .attr('r', d => {
      switch (d.label) {
        case '行政级别': return 16
        case '城市': return 14
        case '省份': return 12
        default: return 14
      }
    })
    .attr('fill', d => {
      switch (d.label) {
        case '行政级别': return colors[0]
        case '省份': return colors[1]
        case '城市': return colors[2]
        default: return colors[2]
      }
    })
    .attr('stroke', '#fff')
    .attr('name', d => d.properties.name || d.properties.level || d.properties.province || '')
    .attr('id', d => d.id)
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended))

  const text = svg.append('g').attr('class', 'texts')
    .selectAll('text').data(nodes).enter()
    .append('text')
    .attr('font-size', '12px')
    .attr('fill', d => {
      switch (d.label) {
        case '行政级别': return colors[0]
        case '省份': return colors[1]
        case '城市': return colors[2]
        default: return colors[2]
      }
    })
    .attr('name', d => d.properties.name || d.properties.level || d.properties.province || '')
    .text(d => d.properties.name || d.properties.level || d.properties.province || '')

  simulation.nodes(nodes).on('tick', ticked)
  simulation.force('link').links(links).distance(d => {
    let dist = 60
    switch (d.source.label) {
      case '行政级别': dist += 30; break
      case '省份': dist += 25; break
      case '城市': dist += 20; break
    }
    switch (d.target.label) {
      case '行政级别': dist += 30; break
      case '省份': dist += 25; break
      case '城市': dist += 20; break
    }
    return dist
  })

  function ticked() {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)
    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)
    text.attr('transform', d => 'translate(' + (d.x - 6) + ',' + (d.y + 6) + ')')
  }

  node.on('mouseenter', function(event, d) {
    const name = d.properties.name || d.properties.level || d.properties.province || ''
    const fill = d3.select(this).attr('fill')

    d3.select('#info').select('h4').style('color', fill).text(name)
    d3.select('#info').selectAll('p').remove()

    for (const key in d.properties) {
      d3.select('#info').append('p').html('<span>' + key + '</span>' + d.properties[key])
    }

    d3.select(svgEl.value).selectAll('.nodes circle').attr('class', function(n) {
      const nName = n.properties.name || n.properties.level || n.properties.province || ''
      if (nName === name) return ''
      for (const l of links) {
        const sName = l.source.properties?.name || l.source.properties?.level || ''
        const tName = l.target.properties?.name || l.target.properties?.level || ''
        if ((sName === name && l.target.id === n.id) || (tName === name && l.source.id === n.id)) return ''
      }
      return 'inactive'
    })

    d3.select(svgEl.value).selectAll('.links line').attr('class', function(l) {
      const sName = l.source.properties?.name || l.source.properties?.level || ''
      const tName = l.target.properties?.name || l.target.properties?.level || ''
      if (sName === name || tName === name) return ''
      return 'inactive'
    })
  })

  node.on('mouseleave', function() {
    d3.select(svgEl.value).selectAll('.nodes circle').attr('class', '')
    d3.select(svgEl.value).selectAll('.links line').attr('class', '')
  })

  d3.select('#mode').selectAll('span').on('click', function() {
    d3.select('#mode').selectAll('span').classed('active', false)
    d3.select(this).classed('active', true)
    if (d3.select(this).text() === '图形') {
      d3.select(svgEl.value).selectAll('.texts text').style('display', 'none')
      d3.select(svgEl.value).selectAll('.nodes circle').style('display', '')
    } else {
      d3.select(svgEl.value).selectAll('.texts text').style('display', '')
      d3.select(svgEl.value).selectAll('.nodes circle').style('display', 'none')
    }
  })
}

function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

function dragged(event, d) {
  d.fx = event.x
  d.fy = event.y
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}

async function doSearch() {
  if (!queryText.value.trim()) return
  searching.value = true
  answer.value = ''
  try {
    const res = await fetch('/api/graph/answer?q=' + encodeURIComponent(queryText.value))
    const data = await res.json()
    if (data.ok) {
      answer.value = data.answer || '未找到相关答案'
    } else {
      answer.value = '查询失败：' + data.error
    }
  } catch (e) {
    answer.value = '查询失败：' + e.message
  } finally {
    searching.value = false
  }
}
</script>

<style scoped>
.graph-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 16px;
  gap: 16px;
}

.graph-header h1 {
  color: #fff;
  font-size: 22px;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
  margin: 0;
}

.graph-container {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

.graph-main {
  flex: 1;
  background: rgba(255,255,255,0.95);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.graph-scroll {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

.graph-scroll svg {
  display: block;
}

.sidebar {
  width: 260px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-card {
  background: rgba(255,255,255,0.95);
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.sidebar-card h3 {
  font-size: 13px;
  color: #1d2129;
  margin-bottom: 10px;
  font-weight: 600;
}

#indicator div {
  margin-bottom: 5px;
  font-size: 12px;
  color: #606770;
}

#indicator span {
  display: inline-block;
  width: 18px;
  height: 11px;
  border-radius: 3px;
  margin-right: 6px;
  vertical-align: middle;
}

#mode {
  display: flex;
  gap: 0;
  margin-top: 10px;
}

#mode span {
  padding: 5px 12px;
  border: 1px solid #e1e4e8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

#mode span:first-child {
  border-radius: 6px 0 0 6px;
}

#mode span:last-child {
  border-radius: 0 6px 6px 0;
  border-left: none;
}

#mode span.active {
  background: #0084ff;
  color: #fff;
  border-color: #0084ff;
}

#mode span:not(.active):hover {
  background: #f0f8ff;
}

#info {
  font-size: 11px;
}

#info h4 {
  margin: 0;
  font-size: 13px;
}

#info p {
  color: #606770;
  margin: 3px 0;
}

#info p span {
  color: #1d2129;
  margin-right: 6px;
  font-weight: 500;
}

.search-box {
  display: flex;
  gap: 6px;
}

.search-box input {
  flex: 1;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 12px;
  outline: none;
}

.search-box input:focus {
  border-color: #0084ff;
}

.search-box button {
  background: #0084ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 7px 12px;
  font-size: 12px;
  cursor: pointer;
}

.search-box button:hover:not(:disabled) {
  background: #0073e6;
}

.search-box button:disabled {
  opacity: 0.6;
}

#answer-result {
  margin-top: 10px;
  padding: 8px;
  background: #f7f8fa;
  border-radius: 6px;
  font-size: 11px;
  color: #1d2129;
  line-height: 1.5;
  max-height: 150px;
  overflow-y: auto;
  white-space: pre-wrap;
}

:deep(.links line) {
  stroke: #ccc;
  stroke-opacity: 0.6;
}

:deep(.links line.inactive) {
  stroke-opacity: 0;
}

:deep(.nodes circle) {
  stroke: #fff;
  stroke-width: 1.5px;
  cursor: pointer;
}

:deep(.nodes circle.inactive) {
  display: none;
}

:deep(.texts text) {
  font-size: 11px;
  cursor: pointer;
  display: none;
}

:deep(.texts text.inactive) {
  display: none;
}
</style>

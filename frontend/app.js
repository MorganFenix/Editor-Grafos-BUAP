/**
 * GraphLab Studio - Client Controller
 * Proyecto: Estructuras de Datos y sus Aplicaciones (BUAP)
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

const state = {
    nodes: [],           // [{id, label, x, y}]
    edges: [],           // [{source, target, weight}]
    isDirected: false,
    isWeighted: true,
    maxNodes: 20,
    
    // Interacción Canvas
    selectedNodeId: null,
    draggingNode: null,
    dragOffsetX: 0,
    dragOffsetY: 0,
    mode: 'add_node',    // 'add_node', 'add_edge', 'select', 'delete'
    
    // Animación de Algoritmos
    activeAlgorithm: 'dijkstra',
    algorithmSteps: [],
    currentStepIndex: 0,
    isPlaying: false,
    animationTimer: null,
    animationSpeed: 1000
};

let canvas, ctx;

document.addEventListener('DOMContentLoaded', () => {
    initCanvas();
    renderMatrixStructure();
    setupEventListeners();
    fetchGraphState();
});

/* ==========================================================================
   1. CANVAS HTML5 & INTERACCIÓN DE RATÓN (DIBUJO Y DRAG & DROP)
   ========================================================================== */

function initCanvas() {
    canvas = document.getElementById('graphCanvas');
    if (!canvas) return;
    ctx = canvas.getContext('2d');

    setTimeout(resizeCanvas, 100);
    window.addEventListener('resize', resizeCanvas);

    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
}

function resizeCanvas() {
    if (!canvas || !canvas.parentElement) return;
    const parent = canvas.parentElement;
    canvas.width = parent.clientWidth || 600;
    canvas.height = parent.clientHeight || 400;
    drawGraph();
}

function handleMouseDown(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const clickedNode = findNodeAt(x, y);

    if (state.mode === 'add_node') {
        if (!clickedNode) {
            if (state.nodes.length >= state.maxNodes) {
                alert(`Límite alcanzado: El sistema permite hasta ${state.maxNodes} nodos.`);
                return;
            }
            createNodeAPI(x, y);
        }
    } else if (state.mode === 'add_edge') {
        if (clickedNode) {
            if (state.selectedNodeId === null) {
                state.selectedNodeId = clickedNode.id;
                setStatusMessage(`Nodo ${clickedNode.label} seleccionado. Haz clic en el nodo destino para crear la arista.`);
            } else if (state.selectedNodeId !== clickedNode.id) {
                const weightStr = state.isWeighted ? prompt(`Peso para la arista (${getLabel(state.selectedNodeId)} -> ${clickedNode.label}):`, '1.0') : '1.0';
                if (weightStr !== null) {
                    const weight = parseFloat(weightStr);
                    if (!isNaN(weight)) {
                        createEdgeAPI(state.selectedNodeId, clickedNode.id, weight);
                    }
                }
                state.selectedNodeId = null;
                setStatusMessage(`Modo Arista: Selecciona un nodo origen.`);
            } else {
                state.selectedNodeId = null;
                setStatusMessage(`Modo Arista: Selecciona un nodo origen.`);
            }
        } else {
            state.selectedNodeId = null;
            setStatusMessage(`Modo Arista: Selecciona un nodo origen.`);
        }
    } else if (state.mode === 'select') {
        if (clickedNode) {
            state.draggingNode = clickedNode;
            state.dragOffsetX = x - clickedNode.x;
            state.dragOffsetY = y - clickedNode.y;
        }
    } else if (state.mode === 'delete') {
        if (clickedNode) {
            deleteNodeAPI(clickedNode.id);
        }
    }
    drawGraph();
}

function handleMouseMove(e) {
    if (state.mode === 'select' && state.draggingNode) {
        const rect = canvas.getBoundingClientRect();
        state.draggingNode.x = e.clientX - rect.left - state.dragOffsetX;
        state.draggingNode.y = e.clientY - rect.top - state.dragOffsetY;
        drawGraph();
    }
}

function handleMouseUp() {
    state.draggingNode = null;
}

function findNodeAt(x, y) {
    const radius = 25;
    return state.nodes.find(node => {
        const dx = node.x - x;
        const dy = node.y - y;
        return Math.sqrt(dx * dx + dy * dy) <= radius;
    }) || null;
}

function getLabel(nodeId) {
    const n = state.nodes.find(node => node.id === nodeId);
    return n ? n.label : `ID ${nodeId}`;
}

function setStatusMessage(msg) {
    const el = document.getElementById('statusMessage');
    if (el) el.innerText = msg;
}

/* ==========================================================================
   2. DIBUJO Y VISUALIZACIÓN EN CANVAS
   ========================================================================== */

function drawGraph(stepHighlights = null) {
    if (!ctx || !canvas) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // DIBUJAR ARISTAS
    state.edges.forEach(edge => {
        const sourceNode = state.nodes.find(n => n.id === edge.source);
        const targetNode = state.nodes.find(n => n.id === edge.target);
        if (sourceNode && targetNode) {
            let color = '#4cd7f6';
            let width = 2.5;

            if (stepHighlights) {
                if (stepHighlights.evaluated_edge && 
                    ((stepHighlights.evaluated_edge.source === edge.source && stepHighlights.evaluated_edge.target === edge.target) ||
                     (!state.isDirected && stepHighlights.evaluated_edge.source === edge.target && stepHighlights.evaluated_edge.target === edge.source))) {
                    color = stepHighlights.cycle_detected ? '#ffb4ab' : '#6ffbbe';
                    width = 4.5;
                } else if (stepHighlights.mst_edges && stepHighlights.mst_edges.some(e => 
                    (e.source === edge.source && e.target === edge.target) ||
                    (!state.isDirected && e.source === edge.target && e.target === edge.source))) {
                    color = '#4edea3';
                    width = 4.0;
                }
            }

            drawEdge(sourceNode, targetNode, edge.weight, color, width);
        }
    });

    // DIBUJAR NODOS
    state.nodes.forEach(node => {
        let fillColor = '#0a0e17';
        let strokeColor = '#4edea3';
        let textColor = '#4edea3';

        if (node.id === state.selectedNodeId) {
            strokeColor = '#acedff';
            fillColor = '#00424e';
            textColor = '#acedff';
        }

        if (stepHighlights) {
            if (stepHighlights.current_node === node.id) {
                strokeColor = '#acedff';
                fillColor = '#00424e';
                textColor = '#acedff';
            } else if (stepHighlights.visited_nodes && stepHighlights.visited_nodes.includes(node.id)) {
                strokeColor = '#10b981';
                fillColor = '#002113';
                textColor = '#6ffbbe';
            }
        }

        drawNode(node, fillColor, strokeColor, textColor);
    });

    updateCounters();
}

function drawNode(node, fillColor, strokeColor, textColor) {
    const radius = 20;
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = fillColor;
    ctx.fill();
    ctx.lineWidth = 3;
    ctx.strokeStyle = strokeColor;
    ctx.stroke();

    ctx.fillStyle = textColor;
    ctx.font = 'bold 14px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(node.label, node.x, node.y);
}

function drawEdge(source, target, weight, color, strokeWidth) {
    const radius = 20;
    const angle = Math.atan2(target.y - source.y, target.x - source.x);

    const startX = source.x + radius * Math.cos(angle);
    const startY = source.y + radius * Math.sin(angle);
    const endX = target.x - radius * Math.cos(angle);
    const endY = target.y - radius * Math.sin(angle);

    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.strokeStyle = color;
    ctx.lineWidth = strokeWidth;
    ctx.stroke();

    if (state.isDirected) {
        const arrowSize = 10;
        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(endX - arrowSize * Math.cos(angle - Math.PI / 6), endY - arrowSize * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(endX - arrowSize * Math.cos(angle + Math.PI / 6), endY - arrowSize * Math.sin(angle + Math.PI / 6));
        ctx.fillStyle = color;
        ctx.fill();
    }

    if (state.isWeighted) {
        const midX = (startX + endX) / 2;
        const midY = (startY + endY) / 2;
        
        ctx.fillStyle = '#1c1f29';
        ctx.fillRect(midX - 12, midY - 9, 24, 18);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.strokeRect(midX - 12, midY - 9, 24, 18);

        ctx.fillStyle = '#dfe2ef';
        ctx.font = 'bold 11px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(weight.toString(), midX, midY);
    }
}

function updateCounters() {
    const lblNodeCount = document.getElementById('lblNodeCount');
    const lblEdgeCount = document.getElementById('lblEdgeCount');
    if (lblNodeCount) lblNodeCount.innerText = state.nodes.length;
    if (lblEdgeCount) lblEdgeCount.innerText = state.edges.length;

    const selectStart = document.getElementById('selectStartNode');
    if (selectStart) {
        const prevStart = selectStart.value;
        selectStart.innerHTML = '';
        state.nodes.forEach(n => {
            selectStart.innerHTML += `<option value="${n.id}">Nodo ${n.label}</option>`;
        });
        if (prevStart && state.nodes.some(n => n.id == prevStart)) {
            selectStart.value = prevStart;
        }
    }
}

/* ==========================================================================
   3. MATRIZ DE ADYACENCIA 20x20 INTERACTIVA
   ========================================================================== */

function renderMatrixStructure() {
    const tableHeader = document.getElementById('matrixHeader');
    const tableBody = document.getElementById('matrixBody');
    if (!tableHeader || !tableBody) return;

    const labels = Array.from({ length: 20 }, (_, i) => String.fromCharCode(65 + i));

    let headerHTML = '<th class="w-7 h-7 text-label-sm font-label-sm text-outline border border-outline-variant bg-surface-container sticky top-0 left-0 z-20">∂</th>';
    labels.forEach(lbl => {
        headerHTML += `<th class="w-7 h-7 text-label-sm font-label-sm font-bold text-primary border border-outline-variant bg-surface-container/90 sticky top-0 z-10">${lbl}</th>`;
    });
    tableHeader.innerHTML = headerHTML;

    let bodyHTML = '';
    for (let i = 0; i < 20; i++) {
        bodyHTML += `<tr><td class="w-7 h-7 text-label-sm font-label-sm font-bold text-primary border border-outline-variant bg-surface-container sticky left-0">${labels[i]}</td>`;
        for (let j = 0; j < 20; j++) {
            bodyHTML += `<td class="border border-outline-variant/40"><input type="text" id="cell_${i}_${j}" data-row="${i}" data-col="${j}" class="matrix-input" value="∞"></td>`;
        }
        bodyHTML += '</tr>';
    }
    tableBody.innerHTML = bodyHTML;

    document.querySelectorAll('.matrix-input').forEach(input => {
        input.addEventListener('change', handleMatrixCellChange);
    });
}

async function updateMatrixUI() {
    try {
        const res = await fetch(`${API_BASE_URL}/graph/matrix`);
        const data = await res.json();
        const matrix = data.matrix;

        for (let i = 0; i < 20; i++) {
            for (let j = 0; j < 20; j++) {
                const cell = document.getElementById(`cell_${i}_${j}`);
                if (cell) {
                    const val = matrix[i][j];
                    cell.value = (val === null || val === undefined) ? '∞' : val;
                }
            }
        }
    } catch (err) {
        console.error('Error al obtener la matriz del backend:', err);
    }
}

async function handleMatrixCellChange() {
    const matrix = [];
    for (let i = 0; i < 20; i++) {
        const rowArr = [];
        for (let j = 0; j < 20; j++) {
            const cell = document.getElementById(`cell_${i}_${j}`);
            const val = cell ? cell.value.trim() : '∞';
            rowArr.push(val === '∞' || val === '' ? null : parseFloat(val));
        }
        matrix.push(rowArr);
    }

    try {
        const res = await fetch(`${API_BASE_URL}/graph/matrix`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matrix })
        });
        if (res.ok) await fetchGraphState();
    } catch (err) {
        console.error('Error enviando la matriz al backend:', err);
    }
}

/* ==========================================================================
   4. ENDPOINTS REST (FASTAPI)
   ========================================================================== */

async function fetchGraphState() {
    try {
        const res = await fetch(`${API_BASE_URL}/graph`);
        const data = await res.json();
        state.nodes = data.nodes;
        state.edges = data.edges;
        state.isDirected = data.is_directed;
        state.isWeighted = data.is_weighted;
        
        drawGraph();
        updateMatrixUI();
    } catch (err) {
        console.error('Error conectando con FastAPI:', err);
    }
}

async function createNodeAPI(x, y) {
    try {
        const res = await fetch(`${API_BASE_URL}/graph/node`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x, y })
        });
        if (res.ok) await fetchGraphState();
    } catch (err) {
        console.error('Error creando nodo:', err);
    }
}

async function deleteNodeAPI(nodeId) {
    try {
        const res = await fetch(`${API_BASE_URL}/graph/node/${nodeId}`, { method: 'DELETE' });
        if (res.ok) await fetchGraphState();
    } catch (err) {
        console.error('Error eliminando nodo:', err);
    }
}

async function createEdgeAPI(source, target, weight) {
    try {
        const res = await fetch(`${API_BASE_URL}/graph/edge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source, target, weight })
        });
        if (res.ok) await fetchGraphState();
    } catch (err) {
        console.error('Error creando arista:', err);
    }
}

async function clearGraphAPI() {
    if (!confirm('¿Deseas limpiar todo el lienzo y la matriz?')) return;
    try {
        const emptyMatrix = Array.from({ length: 20 }, () => Array(20).fill(null));
        await fetch(`${API_BASE_URL}/graph/matrix`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matrix: emptyMatrix })
        });
        await fetchGraphState();
    } catch (err) {
        console.error('Error al limpiar el grafo:', err);
    }
}

async function setGraphDirection(isDirected) {
    state.isDirected = isDirected;
    const btnDir = document.getElementById('btnToggleDirected');
    const btnUndir = document.getElementById('btnToggleUndirected');

    if (isDirected) {
        btnDir?.classList.add('bg-surface-container-high', 'text-primary', 'font-medium');
        btnDir?.classList.remove('text-on-surface-variant');
        btnUndir?.classList.remove('bg-surface-container-high', 'text-primary', 'font-medium');
        btnUndir?.classList.add('text-on-surface-variant');
    } else {
        btnUndir?.classList.add('bg-surface-container-high', 'text-primary', 'font-medium');
        btnUndir?.classList.remove('text-on-surface-variant');
        btnDir?.classList.remove('bg-surface-container-high', 'text-primary', 'font-medium');
        btnDir?.classList.add('text-on-surface-variant');
    }

    try {
        await fetch(`${API_BASE_URL}/graph/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_directed: isDirected, is_weighted: state.isWeighted })
        });
        await fetchGraphState();
    } catch (err) {
        console.error('Error cambiando dirección del grafo:', err);
    }
}

/* ==========================================================================
   5. EVENTOS, HERRAMIENTAS Y CONTROLADORES DE ANIMACIÓN
   ========================================================================== */

function setupEventListeners() {
    document.getElementById('toolAddNode')?.addEventListener('click', () => setToolMode('add_node', 'NODO', 'toolAddNode', 'Haz clic en el lienzo para agregar nodos (máximo 20).'));
    document.getElementById('toolAddEdge')?.addEventListener('click', () => setToolMode('add_edge', 'ARISTA', 'toolAddEdge', 'Modo Arista: Selecciona un nodo origen.'));
    document.getElementById('toolSelect')?.addEventListener('click', () => setToolMode('select', 'MOVER', 'toolSelect', 'Haz clic y arrastra un nodo para reubicarlo.'));
    document.getElementById('toolDelete')?.addEventListener('click', () => setToolMode('delete', 'ELIMINAR', 'toolDelete', 'Haz clic sobre un nodo para eliminarlo.'));
    document.getElementById('toolClear')?.addEventListener('click', clearGraphAPI);

    document.getElementById('btnToggleDirected')?.addEventListener('click', () => setGraphDirection(true));
    document.getElementById('btnToggleUndirected')?.addEventListener('click', () => setGraphDirection(false));

    document.getElementById('algoDijkstra')?.addEventListener('click', () => setAlgorithm('dijkstra', 'algoDijkstra'));
    document.getElementById('algoKruskal')?.addEventListener('click', () => setAlgorithm('kruskal', 'algoKruskal'));
    document.getElementById('algoPrim')?.addEventListener('click', () => setAlgorithm('prim', 'algoPrim'));
    document.getElementById('algoFloyd')?.addEventListener('click', () => setAlgorithm('floyd-warshall', 'algoFloyd'));

    document.getElementById('btnExecuteAlgo')?.addEventListener('click', executeAlgorithm);
    document.getElementById('btnRunTopBar')?.addEventListener('click', executeAlgorithm);

    document.getElementById('btnPlay')?.addEventListener('click', playAnimation);
    document.getElementById('btnStepNext')?.addEventListener('click', nextStep);
    document.getElementById('btnStepPrev')?.addEventListener('click', prevStep);
    document.getElementById('btnReset')?.addEventListener('click', resetAnimation);
    document.getElementById('btnResetTopBar')?.addEventListener('click', resetAnimation);
}

function setToolMode(mode, label, elementId, statusMsg) {
    state.mode = mode;
    state.selectedNodeId = null;
    
    const activeLabel = document.getElementById('activeModeLabel');
    if (activeLabel) activeLabel.innerText = label;
    if (statusMsg) setStatusMessage(statusMsg);

    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.classList.remove('bg-surface-container-high', 'text-primary', 'border-l-2', 'border-primary');
        btn.classList.add('text-on-surface-variant');
    });

    const activeBtn = document.getElementById(elementId);
    if (activeBtn) {
        activeBtn.classList.add('bg-surface-container-high', 'text-primary', 'border-l-2', 'border-primary');
        activeBtn.classList.remove('text-on-surface-variant');
    }
    drawGraph();
}

function setAlgorithm(algo, elementId) {
    state.activeAlgorithm = algo;
    document.querySelectorAll('.algo-tab').forEach(tab => {
        tab.classList.remove('border-b-2', 'border-primary', 'text-primary', 'bg-surface-container-low');
        tab.classList.add('text-on-surface-variant');
    });
    const currentTab = document.getElementById(elementId);
    if (currentTab) {
        currentTab.classList.add('border-b-2', 'border-primary', 'text-primary', 'bg-surface-container-low');
    }
}

async function executeAlgorithm() {
    try {
        if (state.nodes.length === 0) {
            alert('Agrega al menos un nodo en el lienzo antes de ejecutar un algoritmo.');
            return;
        }

        let url = `${API_BASE_URL}/graph/algorithm/${state.activeAlgorithm}`;
        const startNodeId = document.getElementById('selectStartNode')?.value;
        
        if (state.activeAlgorithm === 'dijkstra' || state.activeAlgorithm === 'prim') {
            if (startNodeId === undefined || startNodeId === null || startNodeId === '') {
                alert('Por favor selecciona un nodo origen válido en la lista.');
                return;
            }
            url += `?start_node=${parseInt(startNodeId)}`;
        }

        const res = await fetch(url, { method: 'GET' });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Error al ejecutar el algoritmo.');
        }

        const steps = await res.json();
        state.algorithmSteps = steps;
        state.currentStepIndex = 0;
        
        const executionLog = document.getElementById('executionLog');
        if (executionLog) {
            executionLog.innerHTML = `<div class="text-primary font-bold">// Algoritmo ${state.activeAlgorithm.toUpperCase()} iniciado (${steps.length} pasos)</div>`;
        }

        renderCurrentStep();
    } catch (err) {
        console.error('Error al ejecutar algoritmo:', err);
        alert(`Error al ejecutar algoritmo: ${err.message}`);
    }
}

function renderCurrentStep() {
    if (state.algorithmSteps.length === 0) return;

    const step = state.algorithmSteps[state.currentStepIndex];
    const isLastStep = (state.currentStepIndex === state.algorithmSteps.length - 1);
    
    const executionLog = document.getElementById('executionLog');
    if (executionLog) {
        let logLine = `<div class="flex items-start gap-2 border-b border-outline-variant/20 py-1">
            <span class="text-secondary font-bold">[PASO ${step.step_number}]</span>
            <span class="text-on-surface">${step.description}</span>
        </div>`;

        // SI ES EL ÚLTIMO PASO, IMPRIMIR EL RESUMEN DESTACADO CON EL COSTO TOTAL
        if (isLastStep) {
            if (state.activeAlgorithm === 'prim' || state.activeAlgorithm === 'kruskal') {
                let totalWeight = 0;
                if (step.mst_edges && step.mst_edges.length > 0) {
                    step.mst_edges.forEach(e => {
                        const found = state.edges.find(edge => 
                            (edge.source === e.source && edge.target === e.target) ||
                            (!state.isDirected && edge.source === e.target && edge.target === e.source)
                        );
                        if (found) totalWeight += found.weight;
                    });
                }
                logLine += `<div class="mt-2 p-2 bg-primary/20 border border-primary rounded text-primary font-bold text-xs shadow-lg">
                    🏆 COSTO TOTAL DEL ÁRBOL (MST): ${totalWeight}
                </div>`;
            } else if (state.activeAlgorithm === 'dijkstra') {
                const startNodeId = parseInt(document.getElementById('selectStartNode')?.value || '0');
                let distSummary = [];
                if (step.updated_distances) {
                    Object.entries(step.updated_distances).forEach(([nodeId, dist]) => {
                        const label = getLabel(parseInt(nodeId));
                        const distStr = (dist === Infinity || dist === null) ? '∞' : dist;
                        distSummary.push(`${label}: ${distStr}`);
                    });
                }
                logLine += `<div class="mt-2 p-2 bg-secondary/20 border border-secondary rounded text-secondary font-bold text-xs shadow-lg">
                    🏁 DISTANCIAS MÍNIMAS DESDE ${getLabel(startNodeId)}:<br>
                    <span class="font-normal text-on-surface">${distSummary.join(' | ')}</span>
                </div>`;
            } else if (state.activeAlgorithm === 'floyd-warshall') {
                logLine += `<div class="mt-2 p-2 bg-tertiary/20 border border-tertiary rounded text-tertiary font-bold text-xs shadow-lg">
                    ✨ MATRIZ DE DISTANCIAS MÍNIMAS (TODOS CONTRA TODOS) CALCULADA CON ÉXITO
                </div>`;
            }
        }

        executionLog.innerHTML += logLine;
        executionLog.scrollTop = executionLog.scrollHeight;
    }

    drawGraph(step);
}

function playAnimation() {
    if (state.isPlaying || state.algorithmSteps.length === 0) return;
    state.isPlaying = true;

    state.animationTimer = setInterval(() => {
        if (state.currentStepIndex < state.algorithmSteps.length - 1) {
            state.currentStepIndex++;
            renderCurrentStep();
        } else {
            pauseAnimation();
        }
    }, state.animationSpeed);
}

function pauseAnimation() {
    state.isPlaying = false;
    if (state.animationTimer) {
        clearInterval(state.animationTimer);
        state.animationTimer = null;
    }
}

function nextStep() {
    pauseAnimation();
    if (state.currentStepIndex < state.algorithmSteps.length - 1) {
        state.currentStepIndex++;
        renderCurrentStep();
    }
}

function prevStep() {
    pauseAnimation();
    if (state.currentStepIndex > 0) {
        state.currentStepIndex--;
        renderCurrentStep();
    }
}

function resetAnimation() {
    pauseAnimation();
    state.currentStepIndex = 0;
    const executionLog = document.getElementById('executionLog');
    if (executionLog) executionLog.innerHTML = '<div class="text-outline-variant">// Consola lista para ejecutar traza algorítmica...</div>';
    drawGraph();
}
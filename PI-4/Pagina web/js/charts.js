// charts.js — Gráficas del panel
// Las variables globales (diasData, totalesData, etc.) las imprime panel.php

// Colores globales para mantener coherencia
const COLORS = {
    primary:  '#0056D2',
    success:  '#00875A',
    danger:   '#DC3545',
    warning:  '#FFC107',
    surface:  '#FFFFFF',
    text:     '#212529',
    muted:    '#6C757D',
};

// Opciones base compartidas por todas las gráficas
const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: { color: COLORS.text, font: { family: 'DM Sans' } }
        }
    },
    scales: {
        x: {
            ticks: { color: COLORS.muted },
            grid:  { color: 'rgba(0,0,0,0.05)' }
        },
        y: {
            ticks: { color: COLORS.muted },
            grid:  { color: 'rgba(0,0,0,0.05)' }
        }
    }
};

// 1. Gráfica de línea — Actividad últimos 7 días
const ctxLinea = document.getElementById('chart-actividad');
if (ctxLinea) {
    new Chart(ctxLinea, {
        type: 'line',
        data: {
            labels: diasData,
            datasets: [{
                label: 'Eventos detectados',
                data: totalesData,
                borderColor: COLORS.primary,
                backgroundColor: 'rgba(0,86,210,0.07)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: COLORS.primary,
                pointRadius: 4,
            }]
        },
        options: {
            ...baseOptions,
            plugins: { ...baseOptions.plugins, title: { display: true, text: 'Actividad últimos 7 días', color: COLORS.text } }
        }
    });
}

// 2. Gráfica de donut — Detectados vs Bloqueados
const ctxDonut = document.getElementById('chart-donut');
if (ctxDonut) {
    new Chart(ctxDonut, {
        type: 'doughnut',
        data: {
            labels: ['Detectados', 'Bloqueados'],
            datasets: [{
                data: [detectadosTotal, bloqueadosTotal],
                backgroundColor: [COLORS.danger, COLORS.success],
                borderWidth: 0,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: COLORS.text, padding: 20 } },
                title:  { display: true, text: 'Ataques detectados vs bloqueados', color: COLORS.text }
            }
        }
    });
}

// 3. Gráfica de barras — Ataques por servicio
const ctxBarras = document.getElementById('chart-servicios');
if (ctxBarras) {
    new Chart(ctxBarras, {
        type: 'bar',
        data: {
            labels: serviciosLabels,
            datasets: [{
                label: 'Ataques por servicio',
                data: serviciosData,
                backgroundColor: [
                    'rgba(0,86,210,0.7)',
                    'rgba(0,135,90,0.7)',
                    'rgba(255,193,7,0.7)',
                ],
                borderRadius: 6,
            }]
        },
        options: baseOptions
    });
}

// 4. Gráfica de área — Porcentaje de éxito (últimos 7 días)
const ctxExito = document.getElementById('chart-exito');
if (ctxExito) {
    new Chart(ctxExito, {
        type: 'bar',
        data: {
            labels: ['Tasa de éxito del sistema'],
            datasets: [{
                data: [exitoPorcentaje],
                backgroundColor: exitoPorcentaje >= 80
                    ? 'rgba(0,135,90,0.7)'
                    : exitoPorcentaje >= 50
                        ? 'rgba(255,193,7,0.7)'
                        : 'rgba(220,53,69,0.7)',
                borderRadius: 8,
            }]
        },
        options: {
            ...baseOptions,
            indexAxis: 'y',
            scales: {
                x: { min: 0, max: 100, ticks: { color: COLORS.muted, callback: v => v + '%' }, grid: { color: 'rgba(0,0,0,0.05)' } },
                y: { ticks: { color: COLORS.muted }, grid: { display: false } }
            },
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Porcentaje de éxito (%)', color: COLORS.text }
            }
        }
    });
}

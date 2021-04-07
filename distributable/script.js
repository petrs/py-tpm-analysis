let files = [
    'dictionary/algorithms.json',
    'dictionary/commands.json',
    'dictionary/ecc.json',
    'lists/fixed_properties.json',
    'lists/performance_metrics.json',
    'lists/supported_algorithms.json',
    'lists/supported_commands.json',
    'lists/supported_ecc.json',
    'data.json',
    'meta.json',
];

let promises = []

for (let file in files) {
    promises.push(
        fetch(files[file])
            .then(response => response.json())
    )
}

Promise.all(promises).then(data => {
    for (let key in data) {
        let name = files[key].split('/').slice(-1)[0].replace('.json', '')
        let tmp = data[key];
        delete data[key];
        data[name] = tmp;
    }

    let table = document.getElementById('table')
    let navigation = document.getElementById('table-navigation')
    let list = document.getElementById('list')
    let loader = document.getElementById('loader')

    table.innerHTML = generateTable(data)
    list.innerHTML = generateList(data)
    navigation.innerHTML = generateNavigation(data)
    loader.innerHTML = ''
})

function generateNavigation(data) {
    let links = [
        'Basic information',
        'Fixed properties',
        'Supported algorithms',
        'Supported commands',
        'Supported ECC',
    ]

    for (let command in data['performance_metrics']) {
        if (data['performance_metrics'].hasOwnProperty(command)) {
            links.push(command)
        }
    }

    let html = 'Goto: '
    links.forEach(link => {
        html += '<a href="#' + link.replace(' ', '_') + '">' + link + '</a>'
    })
    return html
}

function generateList(data) {
    let html = '<h1>Click on each checkbox to show/hide corresponding column (card)</h1><div class="list">'
    data['data'].forEach(column => {
        html += '<div class="list-item"><input class="checkbox" type="checkbox" onchange="toggle(\'column-\' + ' + column['id'] + ')" checked="true" \><span class="bold mr-2">' + column['id'] + '</span> - ' + column['name'] + ' </div>'
    })
    html += '</div><div class="controls">\n' +
'                <div>\n' +
'                    <button onclick="showAll();">Select all</button>\n' +
'                    <button onclick="hideAll();">Deselect all</button>\n' +
'                </div>\n' +
'                <div>\n' +
'                    <button id="download-button" onmousedown="fetchData()">Download data</button>\n' +
'                </div>\n' +
'            </div>'

    return html
}

function hideAll() {
    for (let el of document.querySelectorAll(".checkbox")) {
        if(el.checked) {
            el.onchange()
            el.checked = false
        }
    }
}

function showAll() {
    for (let el of document.querySelectorAll(".checkbox")) {
        if(!el.checked) {
            el.onchange()
            el.checked = true
        }
    }
}

function toggle(name) {
    for (let el of document.querySelectorAll('.' + name)) {
        el.classList.toggle('hidden')
    }
}

function generateTable(data) {
    let html = ''

    html += getHeader('Basic information', data['data'], true, true);

    html += getRow('manufacturer', data['data'])
    html += getRow('firmware', data['data'])
    html += getRow('vendor', data['data'])

    html += getHeader('Fixed properties', data['data']);
    data['fixed_properties'].forEach(property => {
        html += getSupportedRow(property, 'properties_fixed', data, true, false)
    })

    html += getHeader('Supported algorithms', data['data']);
    data['supported_algorithms'].forEach(algorithm => {
        html += getSupportedRow(algorithm, 'supported_algorithms', data)
    })

    html += getHeader('Supported commands', data['data']);
    data['supported_commands'].forEach(command => {
        html += getSupportedRow(command, 'supported_commands', data)
    })

    html += getHeader('Supported ECC', data['data']);
    data['supported_ecc'].forEach(ecc => {
        html += getSupportedRow(ecc, 'supported_ecc', data)
    })

    for (let metric in data['performance_metrics']) {
        if (data['performance_metrics'].hasOwnProperty(metric)) {
            html += getHeader(metric, data['data']);
            for (let test_case in data['performance_metrics'][metric]) {
                if (data['performance_metrics'][metric].hasOwnProperty(test_case)) {
                    html += getPerformanceRow(metric, test_case, data)
                }
            }
        }
    }

    return html;
}

function getRow(name, columns) {
    let string = '<tr class="data-row"><td colspan=2 class="sticky">' + capitalize(name) + '</td>'
    columns.forEach(column => {
        column['dataset'].forEach(dataset => {
            string += '<td class="column-' + column['id'] + ' center ' + (dataset['no_tpm'] ? 'red-cell' : '') + '">' + createTooltip(dataset[name], column) + '</td>'
        })
    })
    string += '</tr>'
    return string
}

function createTooltip(print, column) {
    return '<span class="hoverable">' + print + '<span class="tooltip">' + column['name'] + '</span></span>'
}

function getStatistics(data, set, name) {
    return '<span class="statistics"><span class="bold">' + data['meta'][set][name] + '</span> / ' + data['meta']['total_tpm'] + ' <span class="italic">(' + data['meta']['total'] + ')</span>' + '</span>'
}

function getSupportedRow(name, set, data, value = false, stats = true) {
    let string = '<tr class="data-row">' +
        '<td colspan=' + (stats ? '1' : '2') + ' class="sticky">' + translateHex(name, set, data) + '</td>'
    if (stats) {
        string += '<td class="sticky sticky-metric center">' + getStatistics(data, set, name) + '</td>'
    }
    data['data'].forEach(column => {
        column['dataset'].forEach(dataset => {
            if(value) {
                if(dataset[set].hasOwnProperty(name)) {
                    string += '<td class="column-' + column['id'] + ' center">' + createTooltip(dataset[set][name], column) + '</td>'
                } else {
                    string += '<td class="column-' + column['id'] + ' center ' + (dataset['no_tpm'] ? 'red-cell' : '') + '">' + createTooltip('---', column) + '</td>'
                }
            } else {
                if(dataset[set].includes(name)) {
                    string += '<td class="column-' + column['id'] + ' supported">' + createTooltip('Yes', column) + '</td>'
                } else {
                    if(set === 'supported_ecc' && dataset['inconclusive_ecc']) {
                        string += '<td class="column-' + column['id'] + ' center inconclusive ' + (dataset['no_tpm'] ? 'red-cell' : '') + '">' + createTooltip('?', column) + '</td>'
                    } else {
                        string += '<td class="column-' + column['id'] + ' unsupported ' + (dataset['no_tpm'] ? 'red-cell' : '') + '">' + createTooltip('-', column) + '</td>'
                    }
                }
            }
        })
    })

    string += '</tr>'
    return string
}

function getPerformanceRow(command, test_case, data) {
    let string = ''
    let first = true

    for (let row in data['performance_metrics'][command][test_case]) {
        string += '<tr class="data-row ' + (first ? 'thick-top' : '') + '">'
        if (first) {
            string += '<td class="test-case sticky" rowspan="6">' + test_case + '</td>'
            first = false
        }

        string += '<td class="metric-cell sticky sticky-metric">' + row + '</td>'

        data['data'].forEach(column => {
            column['dataset'].forEach(dataset => {
                try {
                    let css = ''
                    if (row === 'fail' && dataset['performance'][command][test_case][row] > 0) {
                        css = 'failed'
                    }
                    string += '<td class="column-' + column['id'] + ' center ' + css + '">' + createTooltip(dataset['performance'][command][test_case][row], column) + '</td>'
                } catch (e) {
                    string += '<td class="column-' + column['id'] + ' center no-data ' + (dataset['no_tpm'] ? 'red-cell' : '') + '">' + createTooltip('No data', column) + '</td>'
                }
            })
        })
    }

    string += '</tr>'

    return string
}

function getHeader(name, columns, header = false, fileNames = false) {
    let string = '<tr class="gray non-hoverable" id=' + name.replace(' ', '_') + '><td class="sticky gray center header-cell" colspan=2>' + name + '</td>'

    columns.forEach(column => {
        string += '<td class="center column-' + column['id'] + '" colspan="' + column['dataset'].length + '">' + column['id'] + '</td>'
    })

    string += '</tr>'

    if(fileNames) {
        string += '<tr class="gray non-hoverable"><td class="sticky gray center header-cell" colspan=2>Result folder name</td>'
        columns.forEach(column => {
            string += '<td class="center ellipsis column-' + column['id'] + '" colspan="' + column['dataset'].length + '">' + createTooltip(column['original_name'], {name: column['original_name']}) + '</td>'
        })
    }

    string += '<tr class="purple non-hoverable"><td class="sticky purple" colspan=2>Name</td>'

    columns.forEach(column => {
        column['dataset'].forEach(dataset => {
            string += '<td class="data-name cell center ' + (dataset['no_tpm'] ? 'red-cell' : '') + ' column-' + column['id'] + '">' + column['name'] + '</td>'
        })
    })

    string += '</tr>'

    return string
}

function fetchData() {
    fetch('data.json')
        .then(response => response.json())
        .then(resp => {
            let data = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(resp));
            let el = document.createElement('a');
            el.setAttribute("href", data);
            el.setAttribute("download", "data.json");
            el.click();
        })
}

function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1)
}

function translateHex(name, set, data) {
    try {
        switch (set) {
            case 'supported_algorithms':
                return name + ' - ' + data['algorithms'][name]
            case 'supported_commands':
                return name + ' - ' + data['commands'][name]
            case 'supported_ecc':
                return name + ' - ' + data['ecc'][name]
            default:
                return name
        }
    } catch (e) {
        return name
    }
}
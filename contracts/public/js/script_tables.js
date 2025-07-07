

const searchSomething = document.querySelector('.input-group input'),
    table_rows = document.querySelectorAll('tbody tr'),
    table_headings = document.querySelectorAll('thead th');

// // 1. Searching for specific data of HTML table
// document.getElementById('saveProsumer').addEventListener('input', searchTable);

function searchTable() {
    table_rows.forEach((row, i) => {
        let table_data = row.textContent.toLowerCase(),
            search_data = searchSomething.value.toLowerCase();

        row.classList.toggle('hide', table_data.indexOf(search_data) < 0);
        row.style.setProperty('--delay', i / 25 + 's');
    })

    document.querySelectorAll('tbody tr:not(.hide)').forEach((visible_row, i) => {
        visible_row.style.backgroundColor = (i % 2 == 0) ? 'transparent' : '#0000000b';
    });
}

// 2. Sorting | Ordering data of HTML table

table_headings.forEach((head, i) => {
    let sort_asc = true;
    head.onclick = () => {
        table_headings.forEach(head => head.classList.remove('active'));
        head.classList.add('active');

        document.querySelectorAll('td').forEach(td => td.classList.remove('active'));
        table_rows.forEach(row => {
            row.querySelectorAll('td')[i].classList.add('active');
        })

        head.classList.toggle('asc', sort_asc);
        sort_asc = head.classList.contains('asc') ? false : true;

        sortTable(i, sort_asc);
    }
})

function sortTable(column, sort_asc) {
    [...table_rows].sort((a, b) => {
        let first_row = a.querySelectorAll('td')[column].textContent.toLowerCase(),
            second_row = b.querySelectorAll('td')[column].textContent.toLowerCase();

        return sort_asc ? (first_row < second_row ? 1 : -1) : (first_row < second_row ? -1 : 1);
    })
        .map(sorted_row => document.querySelector('tbody').appendChild(sorted_row));
}

// 3. Converting HTML table to PDF

const consumers_table = document.querySelector('#consumers_table');

const { jsPDF } = window.jspdf;

// Unified toPDF function
const toPDF = function (table, fileName) {
    // Create a new jsPDF instance
    const pdf = new jsPDF();

    // Capture the table headers
    const t_heads = [...table.querySelectorAll('th')].map(head => head.textContent.trim());
    
    // Capture the table rows
    const tbody_rows = [...table.querySelectorAll('tbody tr')].map(row => 
        [...row.querySelectorAll('td')].map(cell => cell.textContent.trim())
    );

    // Add table data to PDF (autoTable library is an optional addition for formatting)
    pdf.text(fileName, 10, 10);
    pdf.autoTable({
        head: [t_heads],
        body: tbody_rows,
        startY: 20,
    });

    // Download the PDF
    pdf.save(`${fileName}.pdf`);
};

// Event handler to handle all export buttons
document.addEventListener('DOMContentLoaded', function() {
    const consumers_table = document.getElementById('consumers_table');
    const prosumers_table = document.getElementById('prosumers_table');

    // Function to handle PDF download
    function handlePDFDownload(table, filename) {
        toPDF(table, filename);
    }

    // Set up event listeners for both tables with one function
    document.getElementById('toPDFProsumer')?.addEventListener('click', () => handlePDFDownload(prosumers_table, "prosumers"));
    document.getElementById('toPDFConsumer')?.addEventListener('click', () => handlePDFDownload(consumers_table, "consumers"));
});


// 4. Converting HTML table to JSON

// Unified toJSON function
const toJSON = function (table) {
    const t_heads = [...table.querySelectorAll('th')].map(head => head.textContent.trim().toLowerCase().replace(/\s/g, '').replace(/↑/g, '')); // Create JSON-friendly keys and replace unusual characters
    const table_data = [...table.querySelectorAll('tbody tr')].map(row => {
        const row_data = {};
        row.querySelectorAll('td').forEach((cell, index) => {
            row_data[t_heads[index]] = cell.textContent.trim();
        });
        return row_data;
    });
    return JSON.stringify(table_data, null, 4); // Format JSON with indentation
};

// Event handler to handle all export buttons
document.addEventListener('DOMContentLoaded', function() {
    const consumers_table = document.getElementById('consumers_table');
    const prosumers_table = document.getElementById('prosumers_table');

    // Function to handle JSON download
    function handleJSONDownload(table, filename) {
        const json = toJSON(table);
        downloadFile(json, 'json', filename);
    }

    // Set up event listeners for both tables with one function
    document.getElementById('toJSONProsumer')?.addEventListener('click', () => handleJSONDownload(prosumers_table, "prosumers"));
    document.getElementById('toJSONConsumer')?.addEventListener('click', () => handleJSONDownload(consumers_table, "consumers"));
});

// 5. Converting HTML table to CSV File

// Unified toCSV function
const toCSV = function (table) {
    const t_heads = table.querySelectorAll('th');
    const tbody_rows = table.querySelectorAll('tbody tr');

    // Create CSV headings
    const headings = [...t_heads].map(head => {
        let actual_head = head.textContent.trim().split(' ');
        return actual_head.splice(0, actual_head.length - 1).join(' ').toLowerCase();
    }).join(',') + ',';

    // Map through each row, capturing the cells' data and any image URLs
    const table_data = [...tbody_rows].map(row => {
        const cells = row.querySelectorAll('td');
        const imgElement = row.querySelector('img');
        const img = imgElement ? decodeURIComponent(imgElement.src) : '';  // Empty if no img present
        const data_without_img = [...cells].map(cell => cell.textContent.replace(/,/g, ".").trim()).join(',');

        return data_without_img + ',' + img;
    }).join('\n');

    return headings + '\n' + table_data;
}

// Event handler to handle all export buttons
document.addEventListener('DOMContentLoaded', function() {
    const consumers_table = document.getElementById('consumers_table');
    const prosumers_table = document.getElementById('prosumers_table');

    // Function to handle CSV download
    function handleCSVDownload(table, filename) {
        const csv = toCSV(table);
        downloadFile(csv, 'csv', filename);
    }

    // Set up event listeners for both tables with one function
    document.getElementById('toCSVProsumer')?.addEventListener('click', () => handleCSVDownload(prosumers_table, "prosumers"));
    document.getElementById('toCSVConsumer')?.addEventListener('click', () => handleCSVDownload(consumers_table, "consumers"));
});

// Function to trigger file download
function downloadFile(content, fileType, fileName) {
    const blob = new Blob([content], { type: `text/${fileType}` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${fileName}.${fileType}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}


let prosumer_id = 0;
let consumer_id = 0;

// Add a new prosumer entry to the table
document.addEventListener('DOMContentLoaded', function() {
document.getElementById('saveProsumer').addEventListener('click', function() {
    const prosumer_name = document.getElementById('prosumer_name').value;
    const prosumer_address = document.getElementById('prosumer_address').value;
    const prosumer_capacity = document.getElementById('prosumer_capacity').value;
    const offerPrice = document.getElementById('prosumer_offer_price').value;

    if (prosumer_name && prosumer_address && prosumer_capacity && offerPrice) {
        const tableBody = document.getElementById('prosumers_table_body');
        const newRow = document.createElement('tr');
        
        prosumer_id += 1;

        newRow.innerHTML = `
            <td>P${prosumer_id}</td> 
            <td>${prosumer_name}</td>
            <td>${prosumer_capacity}</td>
            <td>${offerPrice}</td>
            <td><p class="status pending">Pending</p></td>
        `;
        
        tableBody.appendChild(newRow);

        // document.getElementById('prosumerForm').reset(); // Reset the form
        // document.getElementById('prosumerForm').style.display = 'none'; // Hide the form
    } else {
        alert('Please fill out all fields');
    }
});

});

// Add a new consumer entry to the table
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('saveConsumer').addEventListener('click', function() {
        const consumer_name = document.getElementById('consumer_name').value;
        const consumer_address = document.getElementById('consumer_address').value;
        const consumer_demand = document.getElementById('consumer_demand').value;
        const consumer_bid = document.getElementById('consumer_bid_price').value;
    
        if (consumer_name && consumer_address && consumer_demand && consumer_bid) {
            const tableBody = document.getElementById('consumers_table_body');
            const newRow = document.createElement('tr');
            
            consumer_id += 1;
    
            newRow.innerHTML = `
                <td>C${consumer_id}</td> 
                <td>${consumer_name}</td>
                <td>${consumer_demand}</td>
                <td>${consumer_bid}</td>
                <td><p class="status pending">Pending</p></td>
            `;
            
            tableBody.appendChild(newRow);
    
            // document.getElementById('prosumerForm').reset(); // Reset the form
            // document.getElementById('prosumerForm').style.display = 'none'; // Hide the form
        } else {
            alert('Please fill out all fields');
        }
    });
    
});

// const socket = io();   // no need of declaring in this file, present in script of energy_marketplace.html file

// prosumer imported file
document.addEventListener('DOMContentLoaded', function () {

    // File input listener
    const fileInput = document.getElementById('import-file-prosumer');

    if (fileInput) {
        fileInput.addEventListener('change', async function (event) {
            const file = event.target.files[0];
            if (!file) return;

            const allowedExtensions = ['csv', 'xlsx'];
            const fileExtension = file.name.split('.').pop().toLowerCase();

            if (!allowedExtensions.includes(fileExtension)) {
                alert('Invalid file type. Please upload a .csv or .xlsx file.');
                fileInput.value = ''; // Clear the file input
                return;
            }

            try {
                if (fileExtension === 'csv') {
                    await processCSVFile(file);
                } else if (fileExtension === 'xlsx') {
                    await processXLSXFile(file);
                }
            } catch (error) {
                console.error('Error processing file:', error);
                alert('An error occurred while processing the file.');
            }
        });
    }

    // Function to process CSV file
    async function processCSVFile(file) {
        const reader = new FileReader();

        reader.onload = function (event) {
            const csvContent = event.target.result;
            const rows = csvContent.split('\n').map(row => row.split(','));

            if (rows.length > 1) {
                rows.forEach((row, index) => {
                    if (index === 0) return; // Skip header row
                    addRowToTable(row[0], row[1], row[2], row[3]);
                });
            }
        };

        reader.readAsText(file);
    }

    // Function to process XLSX file
    async function processXLSXFile(file) {
        const reader = new FileReader();

        reader.onload = async function (event) {
            const data = new Uint8Array(event.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            const sheet = workbook.Sheets[sheetName];
            const json = XLSX.utils.sheet_to_json(sheet);

            json.forEach(row => {
                const { 'prosumer name': name, 'prosumer address': address, 'prosumer capacity': capacity, 'prosumer offer': offer } = row;
                if (name && address && capacity && offer) {
                    addRowToTable(name, address, capacity, offer);
                }
            });
        };

        reader.readAsArrayBuffer(file);
    }

    // Function to add a new row to the table
    function addRowToTable(prosumer_name, prosumer_address, prosumer_capacity, prosumer_offer) {
        const tableBody = document.getElementById('prosumers_table_body');
        const newRow = document.createElement('tr');

        prosumer_id += 1;

        newRow.innerHTML = `
            <td>P${prosumer_id}</td> 
            <td>${prosumer_name}</td>
            <td>${prosumer_capacity}</td>
            <td>${prosumer_offer}</td>
            <td><p class="status pending">Pending</p></td>
        `;

        tableBody.appendChild(newRow);

        // Emit the prosumer data to the server
        socket.emit('add_prosumer', {
            prosumer_id: prosumer_id,
            prosumer_name: prosumer_name,
            prosumer_address: prosumer_address,
            prosumer_capacity: prosumer_capacity,
            prosumer_offer_price: prosumer_offer
        });
    }
});


// consumer imported file
document.addEventListener('DOMContentLoaded', function () {

    // File input listener
    const fileInput = document.getElementById('import-file-consumer');

    if (fileInput) {
        fileInput.addEventListener('change', async function (event) {
            const file = event.target.files[0];
            if (!file) return;

            const allowedExtensions = ['csv', 'xlsx'];
            const fileExtension = file.name.split('.').pop().toLowerCase();

            if (!allowedExtensions.includes(fileExtension)) {
                alert('Invalid file type. Please upload a .csv or .xlsx file.');
                fileInput.value = ''; // Clear the file input
                return;
            }

            try {
                if (fileExtension === 'csv') {
                    await processCSVFile(file);
                } else if (fileExtension === 'xlsx') {
                    await processXLSXFile(file);
                }
            } catch (error) {
                console.error('Error processing file:', error);
                alert('An error occurred while processing the file.');
            }
        });
    }

    // Function to process CSV file
    async function processCSVFile(file) {
        const reader = new FileReader();

        reader.onload = function (event) {
            const csvContent = event.target.result;
            const rows = csvContent.split('\n').map(row => row.split(','));

            if (rows.length > 1) {
                rows.forEach((row, index) => {
                    if (index === 0) return; // Skip header row
                    addRowToTable(row[0], row[1], row[2], row[3]);
                });
            }
        };

        reader.readAsText(file);
    }

    // Function to process XLSX file
    async function processXLSXFile(file) {
        const reader = new FileReader();

        reader.onload = async function (event) {
            const data = new Uint8Array(event.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            const sheet = workbook.Sheets[sheetName];
            const json = XLSX.utils.sheet_to_json(sheet);

            json.forEach(row => {
                const { 'consumer name': name, 'consumer address': address, 'consumer demand': demand, 'consumer bid': bid } = row;
                if (name && address && demand && bid) {
                    addRowToTable(name, address, demand, bid);
                }
            });
        };

        reader.readAsArrayBuffer(file);
    }

    // Function to add a new row to the table
    function addRowToTable(consumer_name, consumer_address, consumer_demand, consumer_bid) {
        const tableBody = document.getElementById('consumers_table_body');
        const newRow = document.createElement('tr');

        consumer_id += 1;

        newRow.innerHTML = `
            <td>C${consumer_id}</td> 
            <td>${consumer_name}</td>
            <td>${consumer_demand}</td>
            <td>${consumer_bid}</td>
            <td><p class="status pending">Pending</p></td>
        `;

        tableBody.appendChild(newRow);

        // Emit the consumer data to the server
        socket.emit('add_consumer', {
            consumer_id: consumer_id,
            consumer_name: consumer_name,
            consumer_address: consumer_address,
            consumer_demand: consumer_demand,
            consumer_bid_price: consumer_bid
        });
    }
});
  
// get function calls from button of html page
function add_prosumer()
{
  var prosumer_name        = document.getElementById("prosumer_name").value;
  var prosumer_address     = document.getElementById("prosumer_address").value;
  var prosumer_capacity    = document.getElementById("prosumer_capacity").value;
  var prosumer_offer_price = document.getElementById("prosumer_offer_price").value;

  socket.emit('add_prosumer', {
      prosumer_id          : prosumer_id,
      prosumer_name        : prosumer_name,
      prosumer_address     : prosumer_address,
      prosumer_capacity    : prosumer_capacity,
      prosumer_offer_price : prosumer_offer_price

  });
}

function add_consumer()
{
  var consumer_name      = document.getElementById("consumer_name").value;
  var consumer_address   = document.getElementById("consumer_address").value;
  var consumer_demand    = document.getElementById("consumer_demand").value;
  var consumer_bid_price = document.getElementById("consumer_bid_price").value;

  socket.emit('add_consumer', {
      consumer_id        : consumer_id,
      consumer_name      : consumer_name,
      consumer_address   : consumer_address,
      consumer_demand    : consumer_demand,
      consumer_bid_price : consumer_bid_price

  });
}

function start_auction()
{
  socket.emit('start_auction');
}
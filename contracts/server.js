// Instances //
var app = require('express')();
const path = require('path');
var http = require('http').Server(app);
var io = require('socket.io')(http);
var express = require('express');

app.use(express.static('public'));

// Energy Marketplace Functions
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'energy_marketplace.html'));
});

io.on('connection', function (socket) {
  console.log("A client connected");

  socket.on('add_prosumer', function (data) {
    io.emit('add_prosumer', data);
  });

  socket.on('add_consumer', function (data) {
    io.emit('add_consumer', data);
  });

  socket.on('start_auction', function (data) {
    io.emit('start_auction', 2);
  });

  socket.on('close_connection', function (data) {
    io.emit('close', 2);
  });

  socket.on('data_from_p1', function (data) {
    console.log("Got data from Prosumer 1:", data);
    io.emit('data_from_p1', data); // send to Python script for processing
  });
  socket.on('data_from_p2', function (data) {
    console.log("Got data from Prosumer 2:", data);
    io.emit('data_from_p2', data); // send to Python script for processing
  });
  socket.on('data_from_p3', function (data) {
    console.log("Got data from Prosumer 3:", data);
    io.emit('data_from_p3', data); // send to Python script for processing
  });
  socket.on('data_from_p4', function (data) {
    console.log("Got data from Prosumer 4:", data);
    io.emit('data_from_p4', data); // send to Python script for processing
  });
});

// Start the server
http.listen(5000, () => {
  console.log('Listening on *:5000');
});

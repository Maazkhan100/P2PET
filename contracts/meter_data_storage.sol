// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract meter_data_storage {

    struct meter_reading {
        string timestamp;
        string from;
        string to;
        string active_power;
        string import_energy;
        string export_energy;
    }

    mapping(address => meter_reading[]) public readings;

    modifier authorize(address meter_address) {
        require(msg.sender == meter_address, "Unauthorized access");
        _;
    }

    function store_meter_reading(address meter_address, string memory timestamp, string memory from, string memory to, string memory active_power, string memory import_energy, string memory export_energy) public authorize(meter_address)
    {
        if (readings[meter_address].length == 10) {
            for (uint i = 0; i < 9; i++) {
                readings[meter_address][i] = readings[meter_address][i+1]; // shift elements
            }
            readings[meter_address].pop();
        }

        readings[meter_address].push(meter_reading(timestamp, from, to, active_power, import_energy, export_energy));
    }

    function get_meter_reading(address meter_address) public view returns (meter_reading[] memory)
    {
        return readings[meter_address];
    }

}
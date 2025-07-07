// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// file name and contract name should match
contract SimpleStorage {
    uint256 private storedData;

    function set(uint256 x) public {
        storedData = x;
    }

    // get function is a view function because it should not modify state of the contract
    function get() public view returns (uint256) {
        return storedData;
    }
}

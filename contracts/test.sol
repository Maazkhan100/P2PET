// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract test {
    mapping (address => uint) public balances;

    // Total tokens given to all accounts
    uint public totalTokensGiven;

    // Total tokens used by all accounts
    uint public totalTokensUsed;

    // Mapping to track tokens used by each account
    mapping (address => uint) public tokensUsedByAccount;

    // Increment Energy Tokens in given account
    function update_tokens(address _account, uint amount) public {
        balances[_account] = balances[_account] + amount;
        totalTokensGiven += amount;  // Update the total tokens given
    }

    // Return Energy Token Balance in given account
    function token_balance(address _account) public view returns (uint) {
        return balances[_account];
    }

    // Return Ether Balance in given account
    function eth_balance(address _account) public view returns (uint) {
        return _account.balance;
    }

    // Interface for automated payment
    // Decrements Energy Tokens in given account
    function send_eth(address payable _account, uint amount) public payable {
        require(balances[_account] >= amount, "Insufficient balance");

        balances[_account] -= amount;
        totalTokensUsed += amount;  // Update the total tokens used
        tokensUsedByAccount[_account] += amount;  // Update the tokens used by this account
        _account.transfer(amount);
    }

    // Return total tokens given to all accounts
    function getTotalTokensGiven() public view returns (uint) {
        return totalTokensGiven;
    }

    // Return total tokens used by all accounts
    function getTotalTokensUsed() public view returns (uint) {
        return totalTokensUsed;
    }

    // Return total tokens used by a specific account
    function getTotalTokensUsedByAccount(address _account) public view returns (uint) {
        return tokensUsedByAccount[_account];
    }
}

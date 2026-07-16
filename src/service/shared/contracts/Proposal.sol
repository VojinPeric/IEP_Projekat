// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Proposal {
    address[] public voters;
    mapping(address => bool) public hasVoted;
    uint256 public votesFor;
    uint256 public votesAgainst;

    event Voted(address voter, bool support);

    constructor(address[] memory _voters) {
        voters = _voters;
    }

    function approve() external {
        _vote(true);
    }

    function reject() external {
        _vote(false);
    }

    function _vote(bool support) private {
        require(_isVoter(msg.sender), "Invalid address.");
        require(!_votingEnded(), "Voting ended.");
        require(!hasVoted[msg.sender], "Already voted");

        hasVoted[msg.sender] = true;
        if (support) {
            votesFor++;
        } else {
            votesAgainst++;
        }

        emit Voted(msg.sender, support);
    }

    function _isVoter(address account) private view returns (bool) {
        for (uint256 i = 0; i < voters.length; i++) {
            if (voters[i] == account) {
                return true;
            }
        }
        return false;
    }

    function _votingEnded() private view returns (bool) {
        uint256 majority = voters.length / 2 + 1;
        return votesFor >= majority || votesAgainst >= majority;
    }
}

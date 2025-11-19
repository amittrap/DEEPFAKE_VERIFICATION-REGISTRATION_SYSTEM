// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DeepfakeLogger {
    struct Result {
        bytes32 contentHash;
        string label;
        uint256 confidence;
        uint256 timestamp;
        address recorder;
    }

    mapping(bytes32 => Result) public results;

    event ResultStored(
        bytes32 indexed contentHash,
        string label,
        uint256 confidence,
        uint256 timestamp,
        address indexed recorder
    );

    function storeResult(
        bytes32 _contentHash,
        string calldata _label,
        uint256 _confidence
    ) external {
        require(_confidence <= 10000);
        results[_contentHash] =
            Result(_contentHash, _label, _confidence, block.timestamp, msg.sender);

        emit ResultStored(_contentHash, _label, _confidence, block.timestamp, msg.sender);
    }

    function getResult(bytes32 _contentHash)
        external
        view
        returns (Result memory)
    {
        return results[_contentHash];
    }
}

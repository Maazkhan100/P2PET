// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EnergyTrade {
    enum Role { N_A, Buyer, Seller }
    enum Phase { DataSubmission, Execution, Trading }

    struct ParticipantData {
        address id;
        Role role;
        uint256 energyAmount;
        uint256 pricePerKWh;
    }

    struct ExecutionResult {
        address submitter;
        bytes32 resultHash;
    }

    uint256 public constant TOTAL_PARTICIPANTS = 10;
    ParticipantData[TOTAL_PARTICIPANTS] public participantsList;

    mapping(address => uint256) public addressToSlot;
    uint256 public nextAvailableSlot = 0;
    uint256 public currentRound = 1;
    Phase public currentPhase = Phase.DataSubmission;

    bytes32 public previousHash;
    bytes32 public previousHashExecution;
    bytes32 public finalHash;

    ExecutionResult[5] public submittedResults;
    uint256 public resultSubmissionCount = 0;

    mapping(address => bool) public hasSubmittedResult;
    mapping(bytes32 => uint256) public hashCounts; // should be in memory instead of storage.

    event DataSubmitted(address indexed participant, uint256 slot, Role role, uint256 energy, uint256 price);
    event PhaseChanged(uint256 round, Phase newPhase);

    modifier onlyPhase(Phase requiredPhase) {
        require(currentPhase == requiredPhase, "Not allowed in this phase");
        _;
    }

    constructor() {
        for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
            participantsList[i] = ParticipantData({
                id: address(0),
                role: Role.N_A,
                energyAmount: 0,
                pricePerKWh: 0
            });
        }
    }

    function register() public onlyPhase(Phase.DataSubmission) {
        require(addressToSlot[msg.sender] == 0, "Participant already registered");
        require(nextAvailableSlot < TOTAL_PARTICIPANTS, "No available slots");
        addressToSlot[msg.sender] = nextAvailableSlot;
        nextAvailableSlot+=1;
    }

    // Phase 1
    function submitData(Role _role, uint256 _energyAmount, uint256 _pricePerKWh) public onlyPhase(Phase.DataSubmission) {
        require(addressToSlot[msg.sender] != 0, "Participant not registered");
        uint256 slot = addressToSlot[msg.sender];
        require(participantsList[slot].energyAmount == 0, "Data already submitted in the current round");
            
        participantsList[slot] = ParticipantData({
            id: msg.sender,
            role: _role,
            energyAmount: _energyAmount,
            pricePerKWh: _pricePerKWh
        });

        emit DataSubmitted(msg.sender, slot, _role, _energyAmount, _pricePerKWh);
    }

    function advancePhase() public {
        if (currentPhase == Phase.DataSubmission) {
            currentPhase = Phase.Execution;
        } else if (currentPhase == Phase.Execution) {
            currentPhase = Phase.Trading;
        } else if (currentPhase == Phase.Trading) {
            currentPhase = Phase.DataSubmission;
            currentRound++;

            for (uint256 i = 0; i < TOTAL_PARTICIPANTS; i++) {
                participantsList[i].role = Role.N_A;
                participantsList[i].energyAmount = 0;
                participantsList[i].pricePerKWh = 0;
            }

            for (uint256 i = 0; i < resultSubmissionCount; i++) {
                hasSubmittedResult[submittedResults[i].submitter] = false;
                submittedResults[i].submitter = address(0);
                submittedResults[i].resultHash = bytes32(0);
            }

            resultSubmissionCount = 0;

        }

        emit PhaseChanged(currentRound, currentPhase);
    }

    function hashParticipantsList() public returns (bytes32) {
        bytes memory encodedData;
        for (uint256 i = 0; i<TOTAL_PARTICIPANTS; i++) {
            ParticipantData memory participant = participantsList[i];
            encodedData = abi.encodePacked(
                encodedData,
                participant.id,
                participant.role,
                participant.energyAmount,
                participant.pricePerKWh
            );
        }

        bytes32 currentHash = keccak256(encodedData);
        if (previousHash == bytes32(0)) {
            previousHash = keccak256(abi.encodePacked(currentHash, currentHash));
        } else {
            previousHash = keccak256(abi.encodePacked(previousHash, currentHash));
        }

        return previousHash;
    }

    // Phase 2
    function submitExecutionResult(bytes32 resultHash) public onlyPhase(Phase.Execution) {
        require(resultSubmissionCount <= 5, "Maximum 5 results already submitted.");
        require(!hasSubmittedResult[msg.sender], "You have already submitted a result.");

        submittedResults[resultSubmissionCount] = ExecutionResult({
            submitter: msg.sender,
            resultHash: resultHash
        });

        hasSubmittedResult[msg.sender] = true;
        resultSubmissionCount++;
    }

    function verifyExecutionResult() public onlyPhase(Phase.Execution) returns (bytes32 majorityHash, bool isVerified) {
        uint256 validSubmissions = 0;

        for (uint256 i = 0; i < submittedResults.length; i++) {
            bytes32 h = submittedResults[i].resultHash;
            if (h != bytes32(0)) {
                hashCounts[h]++;
                validSubmissions++;
            }
        }

        if (validSubmissions == 0) {
            return (bytes32(0), false);
        }

        for (uint256 i = 0; i < submittedResults.length; i++) {
            bytes32 h = submittedResults[i].resultHash;
            if (h != bytes32(0) && hashCounts[h] > validSubmissions / 2) {
                if (previousHashExecution == bytes32(0)) {
                    previousHashExecution = keccak256(abi.encodePacked(h, h));
                } else 
                {
                    previousHashExecution = keccak256(abi.encodePacked(previousHashExecution, h));
                }
                finalHash = h;
                return (h, true);
            }
        }

        finalHash = bytes32(0);
        return (bytes32(0), false);
    }
}

import json
import os

import solcx

SOURCE_PATH = os.path.join(
    "src", "service", "shared", "contracts", "Proposal.sol"
)
OUTPUT_PATH = os.path.join(
    "src", "service", "shared", "contracts", "Proposal.json"
)
SOLC_VERSION = "0.8.24"

# EVM version pinned to "istanbul" on purpose: the project runs on
# trufflesuite/ganache-cli:v6.12.2, which does not understand the PUSH0
# opcode introduced by newer EVM targets (Shanghai and later). Compiling
# with a newer default would produce bytecode that reverts with
# "invalid opcode" the moment it is deployed against this Ganache image.
EVM_VERSION = "istanbul"


def main():
    solcx.install_solc(SOLC_VERSION)

    with open(SOURCE_PATH, "r") as file:
        source = file.read()

    compiled = solcx.compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=SOLC_VERSION,
        evm_version=EVM_VERSION,
    )

    # compile_source returns a dict keyed by "<stdin>:ContractName";
    # this file only defines a single contract, so just take the first.
    _, contract_interface = next(iter(compiled.items()))

    artifact = {
        "abi": contract_interface["abi"],
        "bytecode": "0x" + contract_interface["bin"],
    }

    with open(OUTPUT_PATH, "w") as file:
        json.dump(artifact, file, indent=2)
        file.write("\n")

    function_names = [
        item["name"] for item in artifact["abi"] if item.get("type") == "function"
    ]
    print(f"Wrote {OUTPUT_PATH}")
    print(f"Functions: {function_names}")
    print(f"Bytecode length: {len(artifact['bytecode'])} chars")


if __name__ == "__main__":
    main()

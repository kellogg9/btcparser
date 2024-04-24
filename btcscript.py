import sys
import struct
import json
import time
import hashlib

## vtf6hv

## sources: https://docs.python.org/3/library/json.html, OH, https://realpython.com/python-json/,

### helper funcs (written)

# reading in the different value types
def readHash(fileName):
    return fileName.read(32)[::-1].hex()

def readUnsInt4Byte(fileName):
    return struct.unpack('<I', fileName.read(4))[0]

def readUnsInt8Byte(fileName):
    return struct.unpack('<Q', fileName.read(8))[0]

def readCompactSizeInt(fileName):
    size = int.from_bytes(fileName.read(1), byteorder="little")
    if size < 253:      # standard (1 byte)
        return size 
    elif size == 253:
        return struct.unpack('<H', fileName.read(2))[0]
    elif size == 254:
        return struct.unpack('<I', fileName.read(4))[0]
    elif size == 255:
        return struct.unpack('<Q', fileName.read(8))[0]



# for handling transaction section
def transactionParse(fileName):
    transaction = {}

    # header ig?
    transaction['version'] = readUnsInt4Byte(fileName)
    transactionInputCount = readCompactSizeInt(fileName)

    # input subsection
    transaction['inputs'] = []
    for i in range(transactionInputCount):     
        txnInput = {}
        txnInput['prevTXHash'] = readHash(fileName)
        txnInput['outputIndex'] = readUnsInt4Byte(fileName)
        inputScriptSize = readCompactSizeInt(fileName)
        txnInput['signatureScript'] = fileName.read(inputScriptSize).hex()
        txnInput['sequence'] = readUnsInt4Byte(fileName)

        # updating to be reachable from tranasaction section
        transaction['inputs'].append(txnInput)

    transactionOutputCount = readCompactSizeInt(fileName)
    transaction['outputs'] = []

    # output subsection
    for i in range(transactionOutputCount):
        txnOutput = {}
        txnOutput['value'] = readUnsInt8Byte(fileName)        # how many satoshi's to spend
        outputScriptSize = readCompactSizeInt(fileName)
        txnOutput['script'] = fileName.read(outputScriptSize).hex()         # pubkey script
       
        # making reachable
        transaction['outputs'].append(txnOutput)


    transaction['lockTime'] = readUnsInt4Byte(fileName)
    return transaction





# actually parsing the block
def blockParse(fileName):
    block = {}

    # header, size = 80
    block['version'] = readUnsInt4Byte(fileName)
    block['previousHeaderHash'] = readHash(fileName)
    block['merkleRootHash'] = readHash(fileName)
    block['time'] = readUnsInt4Byte(fileName)
    block['nBits'] = fileName.read(4)[::-1].hex()             # slides say this is uint 4 bytes, so idk if this is right
    block['nonce'] = readUnsInt4Byte(fileName)

    

    # transactions section
    txnCount = readCompactSizeInt(fileName)
    block['txnCount'] = txnCount
    block['txns'] = []
    for i in range(txnCount):
        transaction = transactionParse(fileName)
        block['txns'].append(transaction)

    return block




# then reading and organizing the blocks
def readBlocks(fileName):               # reads blocks and puts them all in a blocks[] list, all separated by commas
    magicNum = b'\xf9\xbe\xb4\xd9'
    blocks = []
            
    
    with open(fileName, 'rb') as file:
        while True:
            chunk = file.read(4)

            if not chunk:       # means invalid block
                break

            if chunk != magicNum:       # magic num check (1)
                print ("error 1 block 0")       
                sys.exit(1)

            size = readUnsInt4Byte(file)
            blocks.append(blockParse(file))

    return blocks
    


# header hash function for error 3 check
def hashHeader(block):

    # getting header hash (undoing all the shit i did earlier)
    version = struct.pack('<I', block['version'])
    # print(version.hex())
    previousHeaderHash = bytes.fromhex(block['previousHeaderHash'])[::-1]
    # print(previousHeaderHash.hex())
    merkleRootHash = bytes.fromhex(block['merkleRootHash'])[::-1]
    # print(merkleRootHash.hex())
    time = struct.pack('<I', block['time'])
    # print(time.hex())
    nBits = bytes.fromhex(block['nBits'])[::-1]
    # print(nBits.hex())    
    nonce = struct.pack('<I', block['nonce'])
    # print(nonce.hex())

    header = version + previousHeaderHash + merkleRootHash + time + nBits + nonce
    # double hash header
    hash1 = hashlib.sha256(header).digest()
    hash2 = hashlib.sha256(hash1).digest()

    hash2a = hash2[::-1]



    return hash2a.hex()




def validate(blocks):       # validation function oh yeah
    prevBlock = None
    size = len(blocks)

    for blockCount, block in enumerate(blocks):

        # version (2)
        if block['version'] != 1:
            print(f"Error 2 Block {blockCount}")
            sys.exit(1)

        # prev header hash check - have to skip first block (3)              
        if prevBlock is not None:
            prevBlockHeaderHash = hashHeader(prevBlock)
            # print(prevBlockHeaderHash)            
            # print(block['previousHeaderHash'])
            if prevBlock and block['previousHeaderHash'] != prevBlockHeaderHash:
                print(f"Error 3 Block {blockCount}")
                sys.exit(1)

        # timestamp (4)
        if prevBlock and block['time'] <= prevBlock['time'] - 7200:
            print(f"Error 4 Block {blockCount}")
            sys.exit(1)

        # transaction version (5)
        for transaction in block['txns']:
            if transaction['version'] != 1:
                print(f"Error 5 Block {blockCount}")
                sys.exit(1)
            
        # merkle root (6)
                # could not get
    
        prevBlock = block

    print(f"No errors {size} blocks")
    return 



# json output
def outputJSON(blocks, fileName):
    fileToWrite = f"{fileName}.json"
    
    blocksToJSON = []
    for i, block in enumerate(blocks):
        txnsToJSON = []
        for transaction in block['txns']:
            # transaction formatting
            txnInputsToJSON = [{
                "txn_hash": input['prevTXHash'],
                "index": input['outputIndex'],
                "input_script_size": len(input['signatureScript']) // 2,  
                "input_script_bytes": input['signatureScript'],
                "sequence": input['sequence']
            } for input in transaction['inputs']]
            
            txnOutputsToJSON = [{
                "satoshis": output['value'],
                "output_script_size": len(output['script']) // 2, 
                "output_script_bytes": output['script']
            } for output in transaction['outputs']]
            
            txnsToJSON.append({
                "version": transaction['version'],
                "txn_in_count": len(transaction['inputs']),
                "txn_inputs": txnInputsToJSON,
                "txn_out_count": len(transaction['outputs']),
                "txn_outputs": txnOutputsToJSON,
                "lock_time": transaction['lockTime']
            })

        # full append with formatted stuff
        blocksToJSON.append({
            "height": i,
            "version": block['version'],
            "previous_hash": block['previousHeaderHash'],
            "merkle_hash": block['merkleRootHash'],
            "timestamp": block['time'],
            "timestamp_readable": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(block['time'])),
            "nbits": block['nBits'],
            "nonce": block['nonce'],
            "txn_count": len(block['txns']),
            "transactions": txnsToJSON
        })

    output = {
        "blocks": blocksToJSON,
        "height": len(blocks)
    }

    # output file
    with open(fileToWrite, 'w') as file:
        json.dump(output, file, indent=4)



### main guy to call everything

def main():     
    fileName = sys.argv[1]
    blocks = readBlocks(fileName)
    validate(blocks)
    outputJSON(blocks, fileName)
    

if __name__ == "__main__":
    main()
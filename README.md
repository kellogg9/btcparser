# Bitcoin Blockchain Parser & Validator
This is a program that was made for the CS4501 - Cryptocurrency class at the University of Virginia. This program takes in a file that contains one or more blocks from the Bitcoin blockchain  in binary format. It reads these blocks in, checks the blockchain for a set of possible errors, and then outputs the result in JSON format.

This program only provides exactly one line of output to the standard output: either no errors X blocks or the specific error and block number (e.g. error 5 block 17). In the case of multiple errors, this program terminates on the first discovered error. In addition, it will create a JSON file if there were no errors – if the input file name was blk00000.blk, then it will create a JSON file named blk00000.blk.json. 

The errors are numbered below:
1) Invalid magic number
2) Invalid header version (this parser expects a header version of 1, as that was used for the assignment)
3) Invalid previous header hash (not checked for first block in the file, don't know previous block)
4) Invalid timestamp (expected no earlier than 2 hours from previous block)
5) Invalid transaction version (expecting 1; what was allowed for this assignment)
6) Merkle Tree Hash in header is correct [CURRENLTY NOT FUNCTIONAL]

To run, run the parse.sh file or just run the btscript.py file. For this to work, we used input .txt files of old Bitcoin blockchain files.

Example: ./parse.sh ~/Dropbox/git/ccc/hws/btcparser/blk00000-b0.blk 

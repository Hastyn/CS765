import argparse
from queue import PriorityQueue
import numpy as np
import sys
from graph import *
from structures import Block , Peer , Transaction
import uuid
from utility import *
from visualize import *
from copy import deepcopy
import faulthandler

# All sizes in kiloBITS, speeds in Kilobits per second, time in milliseconds

faulthandler.enable()
sys.setrecursionlimit(10**6)

if __name__=='__main__':

    np.random.seed(0)

    parser = argparse.ArgumentParser()
    parser.add_argument("--peers", help='number of peers',type=int)
    parser.add_argument("--slow", help='percentage of slow nodes',type=float)
    parser.add_argument("--lowcpu", help='percentage of low CPU nodes',type=float)
    parser.add_argument("--meantransactiontime", help='mean time between arrival of transactions in ms',type=float)
    parser.add_argument("--meanblocktime", help='mean time between arrival of blocks in ms',type=float)
    parser.add_argument("--zeta", help='percentage of honest nodes an adversary is connected to',type=float)
    parser.add_argument("--advminingpower", help='percentage of hashing power the adversary has',type=float)
    parser.add_argument("--stubborn", help='stubborn or selfish')
    
    args=parser.parse_args()
    peers=args.peers #Number of peers
    slow=args.slow # Percentage of slow peers
    lowcpu=args.lowcpu # Percentage of lowcpu peers
    meantransactiontime=args.meantransactiontime # Mean transaction time in ms
    meanblocktime=args.meanblocktime # Mean block arrival time in ms
    zeta = args.zeta #Percentage of honest nodes an adversary is connected to
    advhashingpower = args.advminingpower #Percentage of hashing power the adversary has

    if((args.peers is None) or (args.slow is None) or (args.lowcpu is None) or (args.meanblocktime is None) or (args.meantransactiontime is None) or (args.zeta is None)):
        print("usage: python simulator.py [--peers PEERS] [--slow SLOW] [--lowcpu LOWCPU] [--meantransactiontime MEANTRANSACTIONTIME] [--meanblocktime MEANBLOCKTIME] [--zeta ZETA] [--advhashingpower ADVHASHINGPOWER]")
        exit(0)
        
    # Defined format of tasks below
    
    #Priority Queue sorts tasks on basis of increasing order of first element, i.e. time
    is_stubborn = args.stubborn=='true' #boolean parameter true for stubborn mining and false for selfish mining
    print(is_stubborn)
    task_list = PriorityQueue() # [time , peer_ID , type_of_action          , ... ]
                                # [                 'received_block'        , received_from, Block ]
                                # [                 'received_transaction'  , received_from , Transaction ]
                                # [                 'generate_block'        , Block ]
                                # [                 'generate_transaction'  , Transaction ]
    
     
    num_low =(int)(peers*lowcpu/100) #Number of nodes with low cpu capabilities
    adv_hash = advhashingpower/100                         
    low_hash=(1.0-adv_hash)/(num_low+(peers-num_low)*10)
    high_hash=(1-adv_hash)*10.0/(num_low+(peers-num_low)*10)   
    
    #Hashing power defined above to ensure high cpu nodes have 10 times the power of low cpu nodes
     
    peer_list = [Peer(i,'fast','highcpu',high_hash) for i in range(peers)]
    
    #Assigning slow nodes
    
    num =(int)(peers*slow/100)
    ele = np.random.choice(range(peers),num,replace=False) # Choosing a random subset of elements and assigning them as slow 
    
    for i in ele:
        peer_list[i].speed='slow'

    peer_list[0].speed='fast'
    
    #Assigning lowcpu nodes
    
    ele = np.random.choice(range(peers),num_low,replace=False) # Choosing a random subset of elements and assigning them as lowcpu
    
    for i in ele:
        # peer_list[i].speed='lowcpu'
        peer_list[i].hashingpower=low_hash
        # print(i)
        
    peer_list[0].hashingpower = adv_hash
    # Generating the original genesis block
    
    # Giving all nodes a balance of MININGFEE coins ( so that transactions can be initiated)
    
    transactions=[]
    for i in range(peers):
        base=Transaction(-1,i,MININGFEE,8000,uuid.uuid4())
        transactions.append(base)
        
    balances = [MININGFEE for i in range(peers)]
    genesis_block = Block(-1,0,-1,-1,transactions,0,0,balances)
    
    for i in range(peers):
        peer_list[i].received_blocks.append(genesis_block)
            
    # Graph Creation

    edges=graph_creation(peers,zeta)
    while(not graph_connected(edges,peers)):
        edges=graph_creation(peers,zeta)
        
        
    for i in range(peers):
        peer_list[i].neighbors=edges[i]
        
    # Setting speed of light propagation delay
    
    rho = np.random.uniform(10,500)  
    
    # Initializing the task list with transactions and blocks for each node
    
    for i in range(peers):
        # Need a gen_transation for each node to kickstart the transaction_generation process
        newtask=transaction_generation(peer_list[i],find_mining_block(peer_list[i]),meantransactiontime,0)
        task_list.put(newtask)
        # print(newtask)
        
        # Need a gen_block for each node to kickstart the block_generation process
        newtask = block_generation(peer_list[i],meanblocktime,0)
        task_list.put(newtask)
        # dump(newtask[3])
        # print(newtask)

        
    count=0 # Determining point till which to run simulation
    trans=0

    print("--------START------------")
    
    while((not task_list.empty()) and (count<=1000) ):
        
        # Get earliest scheduled task in task list
        
        task=task_list.get()
        # print(task)
        
        # if(task[2] == 'received_block'):
        #     print("Block ID:", task[4].blk_id)
        # elif(task[2] == 'received_transaction'):
        #     print("Transaction ID:",task[4].transaction_id)
        # elif(task[2] == 'gen_block'):
        #     print("Block ID:",task[3].blk_id)
        # else:
        #     print("Transaction ID:",task[3].transaction_id)
        
       
        
        if task[2] == 'received_block':
            
            #If block already reached, skip
            if find_block_depth(task[4].blk_id,peer_list[task[1]]) != -1:
                continue
            
            # Creating copy of block which will be updated
            block = Block(task[4].prev_blk_id,task[4].blk_id,task[4].miner_id,task[1],task[4].transactions,task[4].depth,task[0],task[4].balances)
            
            # Finding the depth of the parent block
            parent_depth = find_block_depth(block.prev_blk_id,peer_list[task[1]])
            
            #If no longer longest chain, drop own block
            if(block.miner_id==peer_list[task[1]].id):
                if(parent_depth<peer_list[task[1]].max_depth):
                    continue
            print(count)
            count+=1 # Incrementing count
            print("Block of "+str(block.miner_id)+" recieved by "+str(task[1])+" blk_ id: "+str(block.blk_id))
            # If parent does not exist, cache block
            
            if parent_depth == -1:
                
                # Making a copy since we should not modify the original block and then appending to cache
                taskcopy = task.copy()
                taskcopy[4]=block
                
                # Adding a received block in cache only once
                if not exists_in_cache(block.blk_id,peer_list[task[1]]):
                    peer_list[task[1]].cacheBlock.append(taskcopy)

                continue
            
            if peer_list[task[1]].id==block.miner_id and block.miner_id==0:
                block.depth=parent_depth+1
                if(validate(block,peer_list[task[1]])):
                # Dont update max depth as this  block is not public,update list of received blocks, along with a sanity check that owner is correct
                    # peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,block.depth)
                    peer_list[task[1]].received_blocks.append(block)
                    assert(block.owner==task[1])
                else:
                    dump(block)
                    print("Validation failed")
                    break
                peer_list[0].lead+=1
                peer_list[0].private_chain.append(block)
                # No broadcasting to neighbours as private chain
                newtask = block_generation(peer_list[task[1]],meanblocktime,task[0])
                task_list.put(newtask)
                continue           
            elif peer_list[task[1]].id==0:
                block.depth=parent_depth+1
                if(validate(block,peer_list[task[1]])):
                # Update list of received blocks, along with a sanity check that owner is correct
                    peer_list[task[1]].received_blocks.append(block)
                    assert(block.owner==task[1])
                else:
                    dump(block)
                    print("Validation failed")
                    break
                
                if peer_list[task[1]].max_depth>=block.depth:
                    # Lead does not change as chain to which block is added is not longest 
                    # add_cache(task_list,peer_list,peer_list[task[1]],block,rho)
                    pass
                else:
                    peer_list[task[1]].max_depth=block.depth
                    # add_cache(task_list,peer_list,peer_list[task[1]],block,rho) to be checked
                    
                    if peer_list[task[1]].lead==1:
                        #Broadcast 1he block in the private chain
                        print("Lead 1 case")
                        for priv_blk in peer_list[task[1]].private_chain:
                            peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,priv_blk.depth)
                            for adjacent in peer_list[task[1]].neighbors:
                                ntask = broadcast_block(task[0],priv_blk,peer_list[task[1]],peer_list[adjacent],rho)
                                task_list.put(ntask)
                        peer_list[task[1]].private_chain = []
                        peer_list[task[1]].lead=0 

                    elif peer_list[task[1]].lead==2:
                        #Broadcast all blocks in private chain
                        print("Lead 2 case")
                        if is_stubborn!=True:
                            for priv_blk in peer_list[task[1]].private_chain:
                                peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,priv_blk.depth)
                                for adjacent in peer_list[task[1]].neighbors:
                                    ntask = broadcast_block(task[0],priv_blk,peer_list[task[1]],peer_list[adjacent],rho)
                                    task_list.put(ntask)
                            peer_list[task[1]].private_chain = []
                            peer_list[task[1]].lead=0 
                        else:
                            peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,peer_list[task[1]].private_chain[0].depth)
                            for adjacent in peer_list[task[1]].neighbors:
                                ntask = broadcast_block(task[0],peer_list[task[1]].private_chain[0],peer_list[task[1]],peer_list[adjacent],rho)
                                task_list.put(ntask)                    
                            peer_list[task[1]].private_chain = peer_list[task[1]].private_chain[1:]
                            peer_list[task[1]].lead-=1 

                    elif peer_list[task[1]].lead>2:
                        print("Lead "+str(peer_list[task[1]].lead)+" case")
                        for adjacent in peer_list[task[1]].neighbors:
                                peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,peer_list[task[1]].private_chain[0].depth)
                                ntask = broadcast_block(task[0],peer_list[task[1]].private_chain[0],peer_list[task[1]],peer_list[adjacent],rho)
                                task_list.put(ntask)                    
                        peer_list[task[1]].private_chain = peer_list[task[1]].private_chain[1:]
                        peer_list[task[1]].lead-=1 
                    
                    else:
                        #Schedule next block generation
                        newtask = block_generation(peer_list[task[1]],meanblocktime,task[0])
                        # print("Added only:- ",newtask)
                        task_list.put(newtask)
                cachetasks = add_cache(task_list,peer_list,peer_list[task[1]],block,rho)
                for cache in cachetasks:
                    task_list.put(cache)
                continue


            # Updating depth of block
            block.depth=parent_depth+1
            
            # Validate transactions of block and update left_transactions of Peer
            if(validate(block,peer_list[task[1]])):
                
                # Updating max depth, list of received blocks, along with a sanity check that owner is correct
                peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,block.depth)
                peer_list[task[1]].received_blocks.append(block)
                assert(block.owner==task[1])
            else:
                dump(block)
                print("Validation failed")
                break
            
            
            # Broadcast to neighbors, except where it is received from
                
            for adjacent in peer_list[task[1]].neighbors:
                if adjacent == task[3]:
                    continue
                ntask = broadcast(task,peer_list[task[1]],peer_list[adjacent],rho)
                task_list.put(ntask)
                # print("Added only:- ",ntask)

            #Cached blocks can be added back now
            add_cache(task_list,peer_list,peer_list[task[1]],block,rho)

            #Schedule next block generation
            newtask = block_generation(peer_list[task[1]],meanblocktime,task[0])
            # print("Added only:- ",newtask)

            task_list.put(newtask)
            
            pass
        elif task[2] == 'received_transaction':
            #If already received, skip rest
            if exists_transaction(task[4].transaction_id,peer_list[task[1]]) != -1:
                continue
            
            # Create new transaction object for adding into list
            
            transaction = Transaction(task[4].start,task[4].destination,task[4].coins,task[4].size,task[4].transaction_id)
            
            # Append to received and left transactions
            peer_list[task[1]].received_transactions.append(transaction)
            
            if(not (exists_transaction_in_blocks(transaction,peer_list[task[1]]))):
                peer_list[task[1]].left_transactions.append(transaction)
            
            # Broadcast to neighbors except where it is received from
            for adjacent in peer_list[task[1]].neighbors:
                if adjacent == task[3]:
                    continue
                ntask = broadcast(task,peer_list[task[1]],peer_list[adjacent],rho)
                task_list.put(ntask)
                # print("Added only:- ",ntask)
                
            pass
        elif task[2] == 'gen_block':
            
            #If not longest chain, stop mining
            if(task[3].depth<peer_list[task[1]].max_depth+1):
                continue
            
            #Validate transaction before receiving, but not update, since updation is done in received_block
            # if(validate_not_update(task[3],peer_list[task[1]])):
            #     pass
            # else:
                
            #     print("Block should be dropped here! Happens in rare cases!")
            #     dump(task[3])
            #     continue
            
            print("Generating block: Miner-"+str(task[1])+" Time-"+str(task[0]))

            #Add received_block task to use the received_block code
            block=deepcopy(task[3])
            newtask=([task[0],task[1],'received_block',task[1],block])
            # print("Added only:- ",newtask)
            
            task_list.put(newtask)
                        
            pass
        elif task[2] == 'gen_transaction':
            
            # Add received_transaction task to use the received_transaction code
            
            newtask=[task[0],task[1],'received_transaction',task[1],task[3]]
            # print("Added only:- ",newtask)
            
            task_list.put(newtask)
            
            # Add a new transaction generation task to keep the cycle going
            
            newtask=transaction_generation(peer_list[task[1]],find_mining_block(peer_list[task[1]]),meantransactiontime,task[0])
            # print("Added only:- ",newtask)
            
            task_list.put(newtask)
            
        else:
            print("ERROR : INVALID TASK TYPE")
            break
        pass


# Finally printing out the received blocks of each of the peers in a separate file

for i in range(peers):
    
    s = f"received_blocks/Peer{i}_Block_Details.out"
    f= open(s,'w')
    
    mining_block = find_mining_block(peer_list[i])
    while(mining_block.blk_id!=0):
        # print(mining_block.blk_id)
        mining_block.main_chain=True
        for blk in peer_list[i].received_blocks:
            if(blk.blk_id==mining_block.prev_blk_id):
                mining_block=blk
                break
    
    adv_main_chain =0
    adv_total =0
    main_chain =0
    total_blocks =0

    for block in peer_list[i].received_blocks:
        if(block.main_chain and block.miner_id==0):
            adv_main_chain+=1
        if(block.main_chain):
            main_chain+=1
        if(block.miner_id==0):
            adv_total+=1
        total_blocks+=1

    print("MPU ADV at node "+str(i)+" is " + str(adv_main_chain/adv_total))
    print("MPU OVERALL at node "+str(i)+" is " + str(main_chain/total_blocks))
    print("ADV blocks in main chain in: "+str(adv_main_chain/main_chain))
    print()

    for block in peer_list[i].received_blocks:
        f.write(str(block.blk_id)+" "+str(block.prev_blk_id)+" "+str(block.time_of_arrival)+" "+str(block.miner_id)+"\n")
        # dump(block)
    f.close()
    # print(s)
    show(s)
    
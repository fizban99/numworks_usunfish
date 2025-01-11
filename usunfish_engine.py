const = lambda x: x 
from random import randint
# Maximum number of moves to keep in the history 
_MAX_HIST = const(10)

###############################################################################
# Helper functions
###############################################################################

def fb64(eb):
    """Decode a base64 encoded string"""
    base64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    dl, ai = (len(eb) * 3) // 4 - eb.count('='), 0
    for i in range(0, len(eb), 4):
        bi = ((base64.index(eb[i])) << 18) | ((base64.index(eb[i+1])&0x3F) << 12) | ((base64.index(eb[i+2])&0x3F) << 6) | base64.index(eb[i+3])&0x3f
        for byte in (bi >> 16, (bi >> 8) & 0xFF, bi & 0xFF):
            if ai < dl: yield int(byte); ai += 1

def b(x):
    """Creates a bytestring from a base64 encoded string"""
    return bytes(fb64(x))

###############################################################################
# Piece-Square tables. Tune these to change sunfish's behaviour
###############################################################################

# The pst tables are encoded in base64 to save space and to allow string interning when possible. 
# the original sunfish values are divied by 4. They fit in 1 byte except for the king values
# The king values have an offset of 14975 
# The max score has then a maximum value with an offset of 32768 (to allow negative values) that fits in 2 bytes
# to make them uint16.
# The following code decodes the psts so that the source code is smaller.
# For the end game, we use the pesto engame table for the king only
pst_b = b('GRkZGRkZGRksLS4rMi0uLxogHiQjICQaFB0YHBwZHBUSGRsbGhkZExMbGhYWGBkUERsXDxAVGREZGRkZGRkZGTU4MzNDODc0RURfPUdVRUJIVkZYWExVRUxMUU9OUExKRUdNS0tORkZBSElLSklIQkBCRkZGRkBBM0A/QEE9QDRBPDs9SjVGQ01VWEVGV1BKTVlIWl1NV0xWVFVYVlZTUlNSVFVUVFBRU1ZWU1JWVVNUVVJRUVFVVE5QTE1MTE1NgH+AeIGAhYSFf4WIhYeAhnyAfoCDfn57d3l7e3x2dXZwb3NydHBscG1wbXFxb3Fsam5wcXBtbGpwcXN5d3Nwb+no5s757v7u6/D35e379u7n8/D3+vjz6Ojk7ezu7eXm5OTn5+jl4+Lg5uXl5OXk4d/j6OPk5OPe3uDg5eDf390aJiQAACgtCREbJicnJhsZCRwKJAggIhELJRsYFBwZDAsODBIMDRcMDQ4OBQkREREYGRUMChQcGh0gGBUaGCMd')
pst_k = b('BhAUFBYcGhQWHRwdHSIeGxsdHhweJCQcFx4fHx8hHxkUGB4fHx4bFhQYGx4eHRoWEhYaHBwaFxQLEBMWEhUTDg==')
inc='\x00\x00\x00\x00\x00'
def g_p(i, xor):
    return pst_b[i^xor]-ord(inc[0])

def g_n(i, xor):
    return pst_b[(i^xor)+64]+ord(inc[1])

def g_b(i, xor):
    return pst_b[(i^xor)+128]-ord(inc[2])

def g_r(i, xor):
    return pst_b[(i^xor)+192]+ord(inc[3])

def g_q(i, xor):
    return pst_b[(i^xor)+256]+ord(inc[4])

def g_k(i, xor):
    return pst_b[(i^xor)+320] +14975 

def g_k_eg(i, xor):
    return pst_k[i^xor] +14975 

pst = [g_p,
         g_n,
         g_b,
         g_r,
         g_q,
         g_k
]



###############################################################################
# Global constants
###############################################################################
# in micropython, const makes the variable a constant, saving memory
# By prepending an underscore to the variable name saves a little bit more memory
# https://docs.micropython.org/en/latest/develop/optimizations.html

_A1 = const(56)
_H1 = const(63)
_A8 = const(0)
_H8 = const(7)

_NO = const(-8)
_E = const(1)
_S = const(8)
_W = const(-1)
_P = const(0)        
_N = const(1)
_B = const(2)
_R = const(3)
_Q = const(4)
_K = const(5)

op_mode = 1


# Our board is represented as a list of 64 integers. Each element represents a square.
# There is no padding, so this diverges from the original sunfish implementation
# each integer is a piece, even numbers for white pieces, odd numbers for black pieces
# The space is 0 or 1 indistinctly (0 when it's white's turn, 1 when it's black's turn)
# The initial board state, encoded in base64 to save space
board = [11, 9, 10, 12, 13, 10, 9, 11, 
         8, 8, 8, 8, 8, 8, 8, 8, 
         6, 6, 6, 6, 6, 6, 6, 6,
         6, 6, 6, 6, 6, 6, 6, 6,
         6, 6, 6, 6, 6, 6, 6, 6,
         6, 6, 6, 6, 6, 6, 6, 6,
         0, 0, 0, 0, 0, 0, 0, 0,
         3, 1, 2, 4, 5, 2, 1, 3]
wc_bc_ep_kp= 1015936
pscore = 0
                    
# Lists of possible moves for each piece type.
# they are encoded in base64 to save space. 
# each byte represents the change in position for a move between -17 and 17. 
# to make it a uint8, it is stored with an offset of 17.
directions = (
'\x02\t\x02\x01\x01\x08\x03\n', 
'\x03\x02\x04\x0b\x04\x1b\x03"\x01 \x00\x17\x00\x07\x01\x00', 
'\x03\n\x03\x1a\x01\x18\x01\x08', 
'\x02\t\x03\x12\x02\x19\x01\x10', 
'\x02\t\x03\x12\x02\x19\x01\x10\x03\n\x03\x1a\x01\x18\x01\x08', 
'\x02\t\x03\x12\x02\x19\x01\x10\x03\n\x03\x1a\x01\x18\x01\x08'
)


# Mate value must be greater than 8*queen + 2*(rook+knight+bishop)
# King value is set to twice this value such that if the opponent is
# 8 queens up, but we got the king, we still exceed MATE_VALUE.
# When a MATE is detected, we'll set the score to MATE_UPPER 
_MT_LW = const(15000 - 10 * 232)
_MT_UP = const(15000 + 10 * 232)

# Constants for tuning search
_QS = const(14)
_QS_A = const(34)
_EVAL_ROUGHNESS = const(4)
_MAX_QS = const(2)
_MAX_DEPTH = const(40)

# Transposition tables
# that prioritize the closest nodes to the main node
# useful for killer heuristics
# useful for storing the score of the closest nodes to the main node
_T_SZS = 154
t_szs = 0
tp_scoreh= [None]*_T_SZS
# preallocate the score table
tp_scored= [None]*_T_SZS*2
max_d_sc = _MAX_DEPTH + _MAX_QS
nodes = 0


##############################################################################3
# Opening book
# The opening book is stored as a sequence of nibbles
# Each nibble is a move index of the possible moves for the current position sorted by score
# A value of 15 is followed by the number of variations after the move. If 0, it's a leaf node
# The opening book contains 1452 plies stored in 1059 bytes from the Balsa_270423.pgn file
# for openings up to 10 pl
###############################################################################
_MAX_OP_D = const(11)
op_ind = 1
op = b('DifjEyIeHo4C4DEeECt+hSAhTyM+BN7S3g5wTgbgzgIhFxfyfgAeACFkPgPn4APgHgHgERDnARAE4JJRBXHgMSsWA3EBBOAeECtkIKIFMA6hLSEi4AEEZoMeAksA6EExYi4AETNO/o5uAuAgAT8wJxDpMiLg004CNeAOAuAuADcxQj5QBnMQJ0zwMjcxQiIOrrXtS/jgAAExQuAeAsTCBSHhIT9uCEXzToMxTlkOA+GuFOEeEOAuG+BKAGRzMRNXMUJ+vhIh4AROAhRiHD7G6hLSEmETFCLgPiXhERLg53LgIi52Ij6AED5QALAeDo4CQrQQEhE8ngLg6AHgcRFsHg5wHhIOUi6FA7QB/sAjr+fgIOAzERAREAPskgMugX4CA2ZHMQ6yJDsUnq6+BeHtS/75Xb5TlJAUIDaeVmQA4K4I4T4C4VcgTRBGRD4gBDu2RzPgREcRNX4TFCYc6kz9IAORAC5D4BMFACLgJ2HOp+vqIUwic5ADHhuXcYNhfh6uCSEREhEt+SeyTtdhSOzh6E4SUBEQAyKVJeAQLnAB4hHgHhPgHgYuLs4FLrwlLhXeDr6CKOjV5OAi5FLg6+U53gtbEvLhouBeHoJV4S4eguvd6OsuAk7LM+k2LgPgUvngNdvswlIuBV3hLo62vuJODk7uCOAh4F6065EyHgXh6+U13nLg5eHtUiUn4F606x4FLhAB9y4ACE0iIg4C9fER4C4AHgYevrJAE+AOn46NguAG8QYhjhEEQwjiAODrHhA44F4M5Afr4VDSEumuVD4XCecwV+QgA/IOAgA/PgTgkALhhJQxJVECAD4ADgDg5VG+8A+gAeAD4CEuGDBGHnEyIuBO0QAQHU4L8vbhHhLhESZSID4OngEuBeA+AhcSAC4EEi4DOTDgAy4RMDvvEDTgTUFBEuYBEy4D7VTgZiZeAeDeAQFuBxkX7iIhEBG36AAeASt+jl4OQhRj9AASHg3ifhF83gKG4FfkEuAm5ODS3gAADggeDOFihelWjgO3GYQ+WhIe/kMuFR1xIRvnEgETdEHlEBKRUA4euecR4Ofk9oUi6e+3IqoAOQAuJeLmABs68A4GGODr4OohTOCuAA5yPsa+COA+ses4NhKS4CtkIE4XPADAAtAuXlFuAB4CeyQeAOvevgAR4Z4C6w/pIY4ELg61YhIjMQ4BJwAhDmmehBJG4G4CQhMC3DABQh5uA3HgI+kSU3FAASHXEOJuDFcRJBPq6eHWHv4Or05uenS+C+x2AC6KTruubgshThEOBuDBYyUyAuHPUbQwCzkiECcYDgLgLglSVuTgEmSODk4CEeTg6Wv2HkGeB+s6++vg7CIRLgJOAc6Ogz95J7jgTr4etz6+BuBhNUIGjgcRzqkhDTAOCb6+DsIh4BAiTgHgfDsiREQQ')
op2 = b('7t4+X8/k/p/m/k4+X8/k/p/m/l4+X8/k/p/m/o4+X8/k/p/m/p4+X8/k/p/m8+Pl/P5P6f5vrj5fz+T+n+b04+X8/k/p/m9ePl/P5P6f5vnj5fz+T+n+b24+X8/k/p/m/m4+X8/k/p/m/n4+X8/k/p/m++Pl/P5P6f5vjj5fz+T+n+b84+X8/k/p/m8=')

def op_get(i, op):
    if i>>1 >= len(op):
        return 0
    return (op[i >> 1] >> ((i & 1) ^ 1) * 4) & 0xF


def parse_sibl(c_ind, d, op):
    if d > _MAX_OP_D:
        return [], c_ind    
    sibl = []
    n_sibl = op_get(c_ind, op)
    # read number of siblings
    if n_sibl == 14 and op_get(c_ind + 1, op) < 4:
        n_sibl = op_get(c_ind + 1, op)+2
        c_ind += 2
    elif n_sibl == 15:
        n_sibl = 0
        c_ind += 1
    elif n_sibl == 14 and op_get(c_ind + 1, op) == 14 and c_ind == 0:
        # 400 move book exception
        n_sibl = 16
        c_ind += 2
    else:
        n_sibl = 1
    for _ in range(n_sibl):
        # read node value
        node = op_get(c_ind, op)
        if node == 14 and op_get(c_ind + 1, op) > 3:
            node = node + op_get(c_ind + 1, op)-4
            c_ind += 1
        c_ind += 1
        sibl.append((node, c_ind))
        # Recursively parse children
        _, c_ind = parse_sibl(c_ind , d+1, op)
    
    return sibl, c_ind



###############################################################################
# Board functions
###############################################################################

def restore(mv, dif):
    """Restore a board from a difference"""
    global board
    board[(mv>>8)&0xFF] = (dif>>4) & 0x0F
    board[mv&0x3F] = dif&0x0F
    if dif > 0XFFFF:
        # castling
        i = (dif>>16)&0xFF
        board[(dif>>8)&0xFF] = board[i]
        board[i] = _R
    elif dif >0xff:
        # en passant
        board[(dif>>8)&0xFF] = _P|8

def ghash():
    global board, pscore, wc_bc_ep_kp
    """Generate a hash from the board
    and store it as a smallint of 31 bits (30 bit + sign bit)
    Since a micropython hash is 16 bits, we need to combine two hashes
    """
    lbrd = board
    h1= bytes((lbrd[i]  << 4) | (lbrd[i+1] ) for i in range(0,64,2))
    h2= bytes(reversed(h1))
    h = ((hash(h1)<<16)|(hash(h2)^(wc_bc_ep_kp<<16)))& 0x7FFFFFFF
    return -(h&0x3FFFFFFF) if h&0x40000000==0x40000000 else h


def reverse():
    """Swap white and black pieces just by flipping
    the highest bit of each nibble and reverse the board"""
    global board
    # for i in range(32):
    #     pos[i], pos[63-i] = pos[63-i]^0x08, pos[i]^0x08

    board =  [x ^ 0x08 for x in reversed(board)]




def rotate_and_set(score, wc, bc, ep, kp, turn, nullmove=False):
      """Rotates the board and sets new values"""
      global board, pscore, wc_bc_ep_kp
      reverse()
      turn = turn^1
      pscore = -score
      wc_bc_ep_kp = (turn<<20)|(bc<<18) | (wc<<16) | (63-ep if ep!=128 and not nullmove else 128)<<8 | (63-kp if kp!=128 and not nullmove else 128)





def rotate(nullmove=False):
      """Rotates the board, preserving enpassant, unless nullmove"""
      global board, pscore, wc_bc_ep_kp
      turn = (wc_bc_ep_kp >>20) 
      wc = (wc_bc_ep_kp>>18) &3
      bc = (wc_bc_ep_kp>>16) & 3
      ep = (wc_bc_ep_kp>>8) & 0xFF
      kp = wc_bc_ep_kp & 0xFF
      rotate_and_set(pscore, wc, bc, ep, kp, turn, nullmove)



###############################################################################
# Chess logic
###############################################################################


def gen_moves(lvalue=-_MT_LW, ccheck=True):
    """A state of a chess game contains:
    board -- a 32 byte representation of the board
    score -- the board evaluation in two bytes with an offset of 32768
    wc -- the castling rights, [west/queen side, east/king side] as the bits 2 and 3 of a byte
    bc -- the opponent castling rights, [west/king side, east/queen side] as the bits 0 and 1 of the same previous byte
    ep - the en passant square as a square number or 128 if there is no en passant square
    kp - the king passant square as a square number or 128 if there is no king passant square
    """
    # For each of our pieces, iterate through each possible 'ray' of moves,
    # as defined in the 'directions' map. The rays are broken e.g. by
    # captures or immediately in case of pieces such as knights.
    global board, directions, pscore, wc_bc_ep_kp
    moves = []  
    ma=moves.append
    lbrd= board
    xor = ((wc_bc_ep_kp>>20))*7
    for i, p in ((i, p) for i, p in enumerate(lbrd) if p<=5):
        # Skip empty squares and opponent's pieces
        iscore = None
        dir = directions[p]
        for dn in range(0, len(dir)-1,2):
            dc, d = ord(dir[dn])  - 2, ord(dir[dn+1]) - 17
            # calculate column for detecting out of bounds
            c = i&7 # equivalent to i % 8
            j = i
            while True:
                j += d
                c += dc
                # Stay inside the board
                # equivalent to if c<0 or c>7 or j<0 or j>63:
                if (c & ~7) | (j & ~63):
                    break
                q = lbrd[j]
                # Stay off friendly pieces
                if q<6:
                    break
  
                # Pawn move, double move and capture
                if p == _P:
                    if d in (_NO, _NO + _NO) and (q |8) != 14: break
                    if d == _NO + _NO and (i < _A1 + _NO or ((lbrd[i + _NO]) |8) != 14): break
                    if (
                        d in (_NO + _W, _NO + _E)
                        and (q|8) == 14
                        and j not in ((wc_bc_ep_kp>>8)&0xFF,wc_bc_ep_kp&0xFF, (wc_bc_ep_kp&0xFF) - 1, (wc_bc_ep_kp&0xFF) + 1)
                    ):
                        break
                    # If we move to the last row, we can be anything but a pawn and a king
                    # so we can store the promotion in the move as the upper 2 bits
                    if _A8 <= j <= _H8:
                        for prom in b"\x01\x02\x03\x04": #NBRQ
                            v, iscore = value(None, i,j,prom,p,q,xor, iscore, ccheck)
                            if iscore==99999:
                                # Return soon if we have a mate or an attack to kp
                                # we set an invalid move 0 to signal a mate
                                return [(v+32768)<<14]
                            elif v >= lvalue:                            
                                ma((i <<8)| j | ((prom-1)<<6)| (v+32768)<<14)
                        break
                # Move it
                v, iscore = value(None, i,j,0,p,q, xor, iscore, ccheck)
                if iscore==99999:
                    # Return soon if we have a mate or an attack to kp
                    # we set an invalid move 0 to signal a mate
                    return [(v+32768)<<14]
                elif v >= lvalue:   
                    ma((i<<8)| j |(v+32768)<<14)
                # Stop crawlers (PNK) from sliding, and sliding after captures
                if p in b'\x00\x01\x05' or  (q<14 and q&8==8):
                    break
                # Castling, by sliding the rook next to the king
                if i == _A1 and ((wc_bc_ep_kp>>18)&2)==2 and j<63 and lbrd[j + _E] == _K :
                    it = j + _E
                    jt = j + _W
                    v,_ = value(None, it,jt,0,_K,6,xor, None, ccheck)
                    if v >= lvalue:
                        ma((it<<8)| jt | (v+32768)<<14)
                    # break since we can't slide beyond the king
                    break
                if i == _H1 and ((wc_bc_ep_kp>>18)&1)==1 and j>0 and lbrd[j + _W] == _K:
                    it = j + _W
                    jt = j + _E
                    v,_ = value(None, it,jt,0,_K,6,xor, None, ccheck)
                    if v >= lvalue:
                        ma((it<<8)| jt | (v+32768)<<14)
                    # break since we can't slide beyond the king
                    break
    moves.sort()
    return moves

def move(mv, val = None):
    global board, pscore, wc_bc_ep_kp

    i, j, prom, turn = mv>>8, mv&63, ((mv&0xFF)>>6)+1,wc_bc_ep_kp >>20
    p = board[i]
    # Copy variables and reset ep and kp
    wc, bc, ep, kp = (wc_bc_ep_kp>>18)&3, (wc_bc_ep_kp>>16) & 3, 128, 128
    val,_ = value(mv, i, j, prom, p, None, None, None) if val is None else (val, None)
    score =  pscore + val
    # Actual move
    dif = (board[i]<<4)| board[j]
    board[j] = p
    board[i] = 6|(turn<<3)
    # Castling rights, we move the rook or capture the opponent's
    wc = wc & 1 if i == _A1 else wc&2 if i == _H1 else wc
    # Black castling rights are inverted
    bc = bc & 2 if j == _A8 else bc&1 if j == _H8 else bc
    # Castling
    if p == _K:
        wc = 0
        if abs(j - i) == 2:
            kp = (i + j) // 2
            k = _A1 if j < i else _H1
            dif = (k<<16)| (kp<<8)|dif
            board[k] = 6|(turn<<3)
            board[kp] = _R
    # Pawn promotion, double move and en passant capture
    elif p == _P:
        if _A8 <= j <= _H8:
            board[j] = prom
        if j - i == 2 * _NO:
            ep = i + _NO
        if j == (wc_bc_ep_kp>>8)&0xFF:
            board [j + _S] = 6|(turn<<3)
            dif = ((j + _S)<<8)|dif
    
    # We rotate the returned position, so it's ready for the next player
    rotate_and_set(score, wc, bc, ep, kp, turn)
    return dif


def value(mv, i, j, prom, p, q, xor, iscore, ccheck=True):
    global board, pscore, wc_bc_ep_kp
    lpst = pst
    q = board[j] if q is None else q  
    xor = ((wc_bc_ep_kp>>20))*7 if xor is None else xor
    # Actual move

    iscore = lpst[p&7](i,xor) if iscore is None else iscore
    scj = lpst[p&7](j, xor)
    score = scj - iscore

    # Capture
    if (q<14 and q&8==8):
        ind = 63 - j 
        score += lpst[q&7](ind, xor) 
    # Castling check detection
    if abs(j - (wc_bc_ep_kp&0xFF)) < 2 and ccheck:
        ind = 63 - j
        score += g_k(ind,xor) 
     # Castling
    if p == _K and abs(i - j) == 2:
        score +=  g_r((i + j)>>1,xor)
        score -=  g_r(_A1 if j < i else _H1,xor)
    # Special pawn stuff
    elif p == _P:
        if _A8 <= j <= _H8:
            score += lpst[prom](j,xor) - g_p(j,xor)
        if j == (wc_bc_ep_kp>>8) & 0xFF:
            score +=  g_p(63 - (j + _S),xor) 
    iscore = 99999 if q|8 == 13 else iscore
    return score, iscore


###############################################################################
# Search logic
###############################################################################



def s_tp(h, mv, e0, e1, d):
    """Store a chunk of data in a hash table
    The hash table has an index list with the 30-bit hashes (smallints),
    the data table has
    tp_score:  ply-depth +best_mv, score,gamma. The depth is stored as 1 byte,
    the mv, score,gamma are stored as 2-byte integers (4bytes). Depth is stored so that nodes closer to the main are
    preferred, and the moves are stored in the order they were found.
    Depth is stored so that nodes closer to the main are
    preferred, and the moves are stored in the order they were found.
    """
    global tp_scoreh, tp_scored, max_d_sc, t_szs

    if t_szs == _T_SZS and d>max_d_sc: 
        return
    try:
        i = tp_scoreh.index(h,0,t_szs)
    except ValueError:
        if t_szs < _T_SZS:
            tp_scoreh[t_szs] = h
            tp_scored[t_szs<<1] = mv|(d<<24)
            tp_scored[(t_szs<<1)+1] = ((e0+32678)<<16)|(e1+32768)
            t_szs += 1
            max_d_sc = max(max_d_sc, d)
            return
        else:
            if d == max_d_sc:
                return
            # replace the first move farther from the main node (higher d)
            maxd = 0
            for i  in range(0, _T_SZS<<1,2):
                curr_d = tp_scored[i]>>24
                if  d < curr_d:
                    tp_scoreh[i>>1] = h
                    # store the depth in the first integer
                    tp_scored[i] =mv|(d<<24)
                    tp_scored[i+1] = (e0+32678)<<16|e1+32768                
                    return  
                else:
                    maxd = max(curr_d, maxd)
            max_d_sc = maxd
        return
    # replace move if it is already in the table
    j = i<<1
    tp_scored[j] = mv|(d<<24)
    tp_scored[j+1] = ((e0+32678)<<16)|(e1+32768)

def reset_tp_score():
    global tp_scored
    for i in range(0,t_szs<<1, 2):
        tp_scored[i+1] = ((-_MT_UP+32678)<<16)|(_MT_UP+32768)


def g_sc(h, d):
    """Get a score from the score table"""
    global tp_scoreh, tp_scored, board
    if d > max_d_sc:
        return 0, (-_MT_UP, _MT_UP)
    try:
        i = tp_scoreh.index(h)
    except ValueError:
        return  0, (-_MT_UP, _MT_UP)
    
   
    sd = tp_scored[i<<1]>>24
    mv = (tp_scored[i<<1]&0xFFFF)
    # try to prevent hash collision
    # by checking if the move starts with a white piece
    if  mv != 0 and board[mv>>8]>5:
        return 0, (-_MT_UP, _MT_UP)  
    # We need to be sure, that the stored search for the score was over the same
    # nodes as the current search.
    if sd != d:
        return mv, (-_MT_UP, _MT_UP)
    e = tp_scored[(i<<1)+1]
    e0 = (e>>16) - 32678
    e1 = (e & 0xFFFF) - 32768
    return mv, (e0, e1)
    
    


def bound(g, od, cn):  
    """ Receives a position, the gamma,depth,can_null, qs and returns the best score for the position
        Let s* be the "true" score of the sub-tree we are searching.
        The method returns r, where
        if gamma >  s* then s* <= r < gamma  (A better upper bound)
        if gamma <= s* then gamma <= r <= s* (A better lower bound) """
    global nodes,  history, board, pscore, wc_bc_ep_kp

    nodes += 1   
    # Depth <= 0 is QSearch. Here any position is searched as deeply as defined by _MAX_QS
    d = max(od, 0)

    # if we reached the maximum depth in quaiescent search, return the score
    sc = pscore
    if od < -_MAX_QS:
        return sc, 0
    # Sunfish is a king-capture engine, so we should always check if we
    # still have a king. Notice since this is the only termination check,
    # the remaining code has to be comfortable with being mated, stalemated
    # or able to capture the opponent king.
    if sc <= -_MT_LW:
        return -_MT_UP, 0

    entry = None
    # hash as a smallint to save memory
    h = ghash() 

    # Look for the strongest move from last time, the hash-move.
    # and look in the table if we have already searched this position before.

    killer, entry = g_sc(h, req_d - od)
    if entry[0] >= g: 
        return entry[0], killer
    if entry[1] < g: 
        return entry[1], 0

    # Let's not repeat positions. We don't check for repetitions:
    # - at the root (can_null=False) since it is in history, but not a draw.
    # - at depth=0, since it would be expensive and break "futulity pruning".
    if cn and d > 0 and h in history:
        return 0, 0
    
    lwc_bc_ep_kp = wc_bc_ep_kp
    # Generator of moves to search in order.
    # This allows us to define the moves, but only calculate them if needed.    
    def moves():
        global wc_bc_ep_kp, pscore, board
        nonlocal killer
        # First try not moving at all. We only do this if there is at least one major
        # piece left on the board, since otherwise zugzwangs are too dangerous.
        # FIXME: We also can't null move if we can capture the opponent king.
        # Since if we do, we won't spot illegal moves that could lead to stalemate.
        # For now we just solve this by not using null-move in very unbalanced positions.
        # TODO: We could actually use null-move in QS as well. Not sure it would be very useful.
        # But still.... We just have to move stand-pat to be before null-move.
        #if depth > 2 and can_null and any(c in pos.board for c in "RBNQ"):
        #if depth > 2 and can_null and any(c in pos.board for c in "RBNQ") and abs(pos.score) < 500:        
        if d > 2 and cn and abs(sc) < 125:
            rotate(True),
            res, best_mv= bound(1-g, od-3, False)
            res = -res
            rotate()
            wc_bc_ep_kp = lwc_bc_ep_kp            
            yield 0, res

        # # For QSearch we have a different kind of null-move, namely we can just stop
        # and not capture anything else.
        if d == 0:
            yield 0, sc
            

        # Is there is no killer move in the kpv
        # try to find one with a more shallow search.
        # This is known as Internal Iterative Deepening (IID). 
        if not killer and d > 2:
            _, killer = bound(g,  d-3, False)
        
        # If depth == 0 we only try moves with high intrinsic score (captures and
        # promotions). Otherwise we do all moves. This is called quiescent search.            
        val_lower = _QS - d * _QS_A 

     
        # Only play the move if it would be included at the current val-limit,
        # since otherwise we'd get search instability.
        # We will skip it the main loop below
        if  killer !=0:
            i, j, prom = killer>>8, killer&63, ((killer&0xFF)>>6)+1
            p, q = board[i], board[j]

            val,_ = value(killer, i, j, prom, p, q, None, None)
            if val >= val_lower:
                dif = move(killer, val)
                res, best_mv = bound(1-g, od-1, True)
                res = -res
                reverse()
                pscore = sc
                wc_bc_ep_kp = lwc_bc_ep_kp
                restore(killer, dif)
                del dif 
                yield killer, res
        else:
            killer = None

        # Then all the other moves in the position. We sort them by the value 
        # and we take them in reverse order to get the best ones first. We also
        # skip the move if it's the killer move, since we already tried that one.
        # we pop the moves from the list, to save memory
        # filtering out the ones that are below the val_lower limit (Quiescent Search).

        gm = gen_moves(val_lower)
        for i in range(len(gm)):
            mv = gm.pop()
            val = (mv>>14)- 32768
            mv = (mv & 0x3FFF) 
            if mv == killer:
                continue
            # If the new score is less than gamma, the opponent will for sure just
            # stand pat, since ""pos.score + val < gamma === -(pos.score + val) >= 1-gamma""
            # This is known as futility pruning.            
            if d < 0 and  sc + val < g:
                del gm
                # Need special case for MATE, since it would normally be caught
                # before standing pat.            
                yield mv, sc + val if val < _MT_LW else _MT_UP
                # We can also break, since we have ordered the moves by value,
                # so it can't get any better than this.                
                return
            if val > _MT_LW:
                #  If the move ends with a king capture, we can stop the search
                # and return the mate score 
                yield mv, _MT_UP
                return
            if od <= -_MAX_QS:
                yield mv, sc+val
            else:
                # old_pos = pos[:]         
                # if mv == 15679:
                #     pass      

                if od <= -_MAX_QS:
                    res = pscore
                else:
                    dif = move(mv, val)
                    res, best_mv = bound(1-g, od-1, True)
                    res = -res
                    reverse()
                    pscore = sc
                    wc_bc_ep_kp = lwc_bc_ep_kp
                    restore(mv, dif)
                    del dif 
                yield mv, res
            
    # Run through the moves, shortcutting when possible        
    best = -_MT_UP
    best_mv = 0
    for mv, score in moves():
        best = max(best, score)
        # Save the move for pv as the distance from the main node 
        #if mv is not None and best==score and od > -_MAX_QS +1 :
            # pv[req_d-od]=[mv]+(pv[req_d-od+1] if pv[req_d-od+1] is not None else []) 
#            best_mv = mv
        if best >= g:
            best_mv = mv
            # Save the move for killer heuristic as the distance from the main node     
            # best_mv = mv
            # if best_mv is not None and od > -_MAX_QS +1 :
            #     assert best_mv==bm[0]
            break





    # Stalemate checking is a bit tricky: Say we failed low, because
    # we can't (legally) move and so the (real) score is -infty.
    # At the next depth we are allowed to just return r, -infty <= r < gamma,
    # which is normally fine.
    # However, what if gamma = -10 and we don't have any legal moves?
    # Then the score is actaully a draw and we should fail high!
    # Thus, if best < gamma and best < 0 we need to double check what we are doing.

    # We will fix this problem another way: We add the requirement to bound, that
    # it always returns MATE_UPPER if the king is capturable. Even if another move
    # was also sufficient to go above gamma. If we see this value we know we are either
    # mate, or stalemate. It then suffices to check whether we're in check.

    # Note that at low depths, this may not actually be true, since maybe we just pruned
    # all the legal moves. So sunfish may report "mate", but then after more search
    # realize it's not a mate after all. That's fair.
    # This is too expensive to test at depth == 0        

    if d > 2 and best == -_MT_UP:
        rotate()
        gm = gen_moves(_MT_UP-1, ccheck=False)
        in_check = (len(gm)==1 and gm[0]&0x3FFF==0)
        rotate()
        if in_check:
            best = -_MT_LW
            best_mv = 0
        else:
            best = 0
            best_mv = 0
        
    # for small transposition tables it is better to store the score in the table 
    # when the score is better than the gamma so that moves and scores can be stored in the 
    # same table
    if best >= g and od > -_MAX_QS +1  and best_mv !=0:
        s_tp(h,best_mv, best,entry[1], req_d- od)

   # if best < g and od > -_MAX_QS +1 :#and best_mv is not None:
   #     s_tp(h,0, entry[0],best, req_d- od)    
    # assert  len(bm) ==0 or best_mv == bm[0]
    return best, best_mv


def mk_mv(mv):
    global last_mv, op_mode, op_ind, ply

    ply += 1
    if op_mode == 1:
        gm = [m&0x3FFF for m in gen_moves()]
        gm.reverse()
        # remove promotion info for the opening comparison
        mv = mv&0x3F3F
        last_mv = gm.index(mv)
        # check if the last move 
        # is in the list of next moves of the opening      
        mvs, _ = parse_sibl(op_ind, ply-1, op)
        i = [i for i, (mv,_) in enumerate(mvs) if mv == last_mv]
        if i:
            # if it is in the list, update the next move index 
            # to the first child of the move
            op_ind = mvs[i[0]][1]
        else:
            # if it is not in the list, exit the opening mode
            op_mode = 0    
       
    return move(mv)

last_mv = -1
ply=0
def g_next_move(op):
    global op_ind, last_mv, op_mode, ply
    # choose a move from the children
    i = op_ind
    mvs, _ = parse_sibl(i, ply, op)
    if not mvs:
        op_mode = 0
        return 0
    mv, _ = mvs[randint(0, len(mvs)-1)]
    mv = gen_moves()[-mv-1]&0x3FFF
    return mv


def search():
    """Iterative deepening MTD-bi search"""
    global nodes, req_d, tp_scored, tp_scoreh,  max_d_sc, board, t_szs, pscore, pst_b, inc, op_ind

    nodes = 0
    # Check if we are in opening mode
    if op_mode==1:
            last_mv = g_next_move(op)
            if last_mv!=0:
                yield 0,pscore-4, pscore, last_mv
                return
    # Check if we have a move from the 400 moves opening book
    if ply == 1:
        op_ind = 0
        last_mv = g_next_move(op2)
        if last_mv!=0:
            yield 0,pscore-4, pscore, last_mv
            return
    g = 0
    # if sum(p&7 for p in board if (p&7) < 11) <= 8:
    if 5 not in [p&7 for p in board] or sum(p&7 for p in board if (p&7) < 5) < 13:
             pst[5] = g_k_eg
    elif ply < 10:
        pst[5] = g_k
    
    inc =chr(randint(0,4)) + chr(randint(0,14)) + chr(randint(0,6)) +chr(randint(0,9)) +chr(randint(0,19))
    # In finished games, we could potentially go far enough to cause a recursion
    # limit exception. Hence we bound the ply. We also can't start at 0, since
    # that's quiscent search, and we don't always play legal moves there.
    # The table of moves is reset at the beginning of the search
    # but shared across all depths
    t_szs = 0
    max_d_sc = 0 
    for req_d in range(1, _MAX_DEPTH+1):
        lower, upper = -_MT_LW, _MT_LW
        while lower < upper - _EVAL_ROUGHNESS:
            score, best_mv= bound(g, req_d, False)
            if score >= g:
                lower = score
            if score < g:
                upper = score
            yield req_d, g, score, best_mv
            g = (lower + upper + 1) // 2
        # Reset the table of scores after each depth
        # keeping the best move from the previous depth
        # and the principal variation
        reset_tp_score()

# Helper functions for user interface

def upd_hist():
    global history, pos
    history.append( ghash())
    if len(history) > _MAX_HIST:
        history.pop(0)

def render(i):
    rank, fil = divmod(i - _A1, 8)
    return chr(fil + ord('a')) + str(-rank + 1)

def render_mv(mv, turn=0):
    if mv ==0:
        return "(none)"    
    i, j = mv>>8, mv&0x3F
    prom = " "
    if j <8 and board[i]|8 == _P+8:
        prom = mapping[((mv>>6)&3)+1]
    if turn ==1:
        i, j = 63 - i, 63 - j       
    return render(i) + render(j) + prom

def can_kill_king(mv, ccheck = True):
    global board, pscore, wc_bc_ep_kp
    # If we just checked for opponent moves capturing the king, we would miss
    # captures in case of illegal castling.
    sc = pscore
    lwc_bc_ep_kp = wc_bc_ep_kp
    if mv != 0:
        dif = move(mv)
    else:
        # if move 0, check if the king is attacked
        rotate()
    res = gen_moves(ccheck=ccheck)
    if mv!=0:
        reverse()
        pscore = sc
        wc_bc_ep_kp = lwc_bc_ep_kp
        restore(mv, dif)
    else:
        rotate()
    if len(res) == 0:
        return False
    if res[0]&0x3FFF ==0:
        return True
    if ccheck:
        return any( abs((m&63) - (wc_bc_ep_kp&0xFF)) < 2 for m in res)
    return False
    
def threefold():
    global history
    return history.count(ghash()) >= 3

def g_trn():
    return wc_bc_ep_kp>>20

pscore, wc_bc_ep_kp = 0, int.from_bytes(b'\x0F\x80\x80',"big")

history = list()
mapping = 'PNBRQK. pnbrqk. '

print("Please run usunfish_chess.py")
bl_info = {
    "name": "2048",
    "author": "Latidoremi",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "N Panel > 2048",
    "description": "2048 Game",
    "category": "Games",
}


from urllib.parse import SplitResult
import bpy, random
import numpy as np


contexts=[
    ('Pause','Pause','',0),
    ('Play','Play','',1),
    ('End','End','',2),
]

def init(context):
    scene = context.scene
    scene.GAME2048_context='Pause'
    context.preferences.addons['2048'].preferences.current_score=0
    
    board = scene.GAME2048_play_board
    count = len(board)
    
    for i in range(count):
        scene.GAME2048_play_board[i]=0
    
    a, b = random.sample(range(16), k=2)
    board[a] = random.choice((2,4))
    board[b] = random.choice((2,4))

def update_ui(context):
    context.preferences.themes[0].view_3d.space.gradients.high_gradient.h+=0


def merge_row(arr, reverse): # False: Left; True:Right
    count = arr.size
    row_score = 0

    if reverse: arr=arr[::-1]
    
    arr_n=[]
    n_idx=[]
    for i in range(count):
        if arr[i]!=0:
            arr_n.append(arr[i])
            n_idx.append(i)
    
    n_count=len(arr_n)
    for i in range(n_count):
        if i<n_count-1 and arr_n[i]==arr_n[i+1]:
            arr_n[i]*=2
            row_score+=arr_n[i]
            arr_n[i+1]=0
    
    for i, n in zip(n_idx, arr_n):
        arr[i] = n
    
    if reverse: arr=arr[::-1]

    return row_score

def reorder_row(arr, reverse): # False: Left; True:Right
    num=[]
    empties=[]
    for i in arr:
        if i!=0:
            num.append(i)
        else:
            empties.append(i)
    
    if not reverse: # Left
        re = num+empties
    else: # Right
        re = empties+num
    
    for i in range(4):
        arr[i] = re[i]

def merge_board(board, reverse):
    score=0
    for row in board:
        row_score = merge_row(row, reverse)
        score += row_score
        reorder_row(row, reverse)
    return score

def join(board, direction):
    if direction=='Right':
        score = merge_board(board, True)
            
    elif direction=='Left':
        score = merge_board(board, False)
            
    elif direction=='Up':
        board = board.T
        score = merge_board(board, False)
        board = board.T
    
    elif direction=='Down':
        board = board.T
        score = merge_board(board, True)
        board = board.T
    return score

def fill_one(board):
    board.shape=(16)

    empty_idx=[]
    for i in range(16):
        if board[i]==0:
            empty_idx.append(i)
    
    if empty_idx:
        sel = random.choice(empty_idx)
        board[sel] = random.choice((2,4))

    board.shape=(4,4)

def check_game_over(board):
    if np.count_nonzero(board==0)!=0:
        return False
    for row in np.row_stack((board, board.T)):
        count=row.size
        for i in range(count):
            if i<count-1 and row[i]==row[i+1]:
                return False
    return True

class GAME2048_OT_play():

    direction:bpy.props.EnumProperty(
        items = [
        ('Up','Up','',0),
        ('Down','Down','',1),
        ('Left','Left','',2),
        ('Right','Right','',3),
        ])
    
    def execute(self, context):
        scene = context.scene

        board_orig = np.array(scene.GAME2048_play_board).reshape((4,4))
        board = board_orig.copy()
        pref = context.preferences.addons['2048'].preferences

        #join
        score = join(board, self.direction)
        pref.current_score += score

        pref.top_score = max((pref.current_score, pref.top_score))
        # print('current_score: ', pref.current_score)

        #check cancelled
        empties=[i for i in scene.GAME2048_play_board if i==0]
        if len(empties)!=0 and np.array_equal(board, board_orig):
            return {'CANCELLED'}
        
        #fill one
        fill_one(board)
        update_ui(context)

        #to scene prop
        for i in range(16):
            scene.GAME2048_play_board[i] = board.flatten()[i]
        
        #check game over
        game_over = check_game_over(board)

        if game_over:
            # print('game over')
            self.report({'INFO'}, 'Game Over')
            scene.GAME2048_context = 'End'

        if context.preferences.addons['2048'].preferences.use_undo:
            bpy.ops.ed.undo_push(message='2048 undo')
        return {'FINISHED'}

class GAME2048_OT_play_bt(bpy.types.Operator, GAME2048_OT_play):
    '''Play'''
    bl_idname = 'game2048.play_bt'
    bl_label = 'Play'
    # bl_options = {'UNDO'}
    
class GAME2048_OT_play_kb(bpy.types.Operator, GAME2048_OT_play):
    '''Play'''
    bl_idname = 'game2048.play_kb'
    bl_label = 'Play'
    bl_options = {'UNDO'}

    def modal(self, context, event):
        if context.scene.GAME2048_context=='End':
            context.area.header_text_set(None)
            return {'FINISHED'}
            
        if event.value == 'PRESS':
            if event.type == 'ESC':
                # print('esc')
                context.scene.GAME2048_context='Pause'
                update_ui(context)
                context.area.header_text_set(None)
                return {'FINISHED'}
            
            elif event.type in {'UP_ARROW','W'}:
                self.direction='Up'
                self.execute(context)
                # print('up arrow')
            
            elif event.type in {'DOWN_ARROW', 'S'}:
                self.direction='Down'
                self.execute(context)
                # print('down arrow')

            elif event.type in {'LEFT_ARROW','A'}:
                self.direction='Left'
                self.execute(context)
                # print('left arrow')
            
            elif event.type in {'RIGHT_ARROW','D'}:
                self.direction='Right'
                self.execute(context)
                # print('right arrow')
            
        if context.preferences.addons['2048'].preferences.use_undo:
            if event.type=='Z' and event.value=='PRESS':
                bpy.ops.ed.undo()

        update_ui(context)
        context.area.header_text_set("Playing 2048...press ESC to quit")
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.scene.GAME2048_context='Play'
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

class GAME2048_OT_new_game(bpy.types.Operator):
    '''New Game'''
    bl_idname = 'game2048.new_game'
    bl_label = 'New Game'
    bl_options = {'UNDO'}
    
    def execute(self, context):
        init(context)
        return {'FINISHED'}

class GAME2048_OT_empty(bpy.types.Operator):
    ''' '''
    bl_idname = 'game2048.empty'
    bl_label = ''
    bl_options = {'UNDO'}
    
    def execute(self, context):
        return {'FINISHED'}


class GAME2048_PT_main_panel(bpy.types.Panel):
    """2048 main panel"""
    bl_category = "2048"
    bl_label = "2048"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    @classmethod
    def poll(cls, context):
        return context.area.ui_type == 'VIEW_3D'
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        pref = context.preferences.addons['2048'].preferences
        input_method = pref.input_method
  
        col=layout.column()
        col.label(text='Top Score: '+str(pref.top_score))
        col.label(text='Current Score: '+str(pref.current_score))

        col = layout.column(align=True)

        if input_method=='Keyboard':
            col.enabled=(scene.GAME2048_context=='Play')
        
        col.scale_y = 2
        for i, item in enumerate(scene.GAME2048_play_board):
            if i%4 ==0:
                sub_row = col.row(align=True)

            sub_row.operator('game2048.empty', text = (str(item) if item!=0 else ''))
        

        if input_method=='Keyboard':
            if scene.GAME2048_context=='Pause':
                layout.operator('game2048.play_kb')
        
        if input_method=='Button':
            row = layout.row(align=True)

            split = row.split()
            split.scale_y=2.5
            split.operator('game2048.play_bt',text='',icon='BACK').direction='Left'

            split = row.split()
            split.scale_y=1.2
            col = split.column()
            col.operator('game2048.play_bt',text='',icon='SORT_DESC').direction='Up'
            col.operator('game2048.play_bt',text='',icon='SORT_ASC').direction='Down'

            split = row.split()
            split.scale_y=2.5
            split.operator('game2048.play_bt',text='',icon='FORWARD').direction='Right'

        if scene.GAME2048_context in {'Pause','End'}:
            layout.operator('game2048.new_game')



class GAME2048_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    use_undo:bpy.props.BoolProperty(name='Use Undo', default=False)
    input_method:bpy.props.EnumProperty(
        description='Input Methods',
        items=[
            ('Button','Button','',0),
            ('Keyboard','Keyboard','',1),
        ],
        default='Button'
        )

    top_score:bpy.props.IntProperty(name='Top Score', default=0, min=0)
    current_score:bpy.props.IntProperty(name='Last Score', default=0, min=0)

    def draw(self, context):
        layout=self.layout

        box = layout.box()
        box.prop(self, 'input_method', text='')
        if self.input_method=='Button':
            box.label(text="Use buttons in the panel to slide and join the numbers")
        elif self.input_method=='Keyboard':
            box.label(text="Hit the 'Play' button to enter play mode, use arrow keys or WASD keys to slide and join the numbers")

        box = layout.box()
        box.prop(self, 'use_undo')
        if self.use_undo:
            if self.input_method=='Button':
                box.label(text="press Ctrl Z to undo")
            elif self.input_method=='Keyboard':
                box.label(text="While in play mode, press Z to undo")

def rand_set(board):
    empties=[]
    for i, n in enumerate(board):
        if n == 0:
            empties.append(i)
    
    sel = random.choice(empties)
    board[sel] = random.choice((2,4))


classes=[
    GAME2048_Preferences,

    GAME2048_OT_play_bt,
    GAME2048_OT_play_kb,
    GAME2048_OT_new_game,
    GAME2048_OT_empty,
    
    GAME2048_PT_main_panel,
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.GAME2048_play_board = bpy.props.IntVectorProperty(name='Play Board', size=16, min=0)
    bpy.types.Scene.GAME2048_context = bpy.props.EnumProperty(items=contexts)
    # init(bpy.context)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    
    del bpy.types.Scene.GAME2048_play_board
    del bpy.types.Scene.GAME2048_context
    
if __name__ == "__main__":
    register()
    
# This is a one file level editor. All classes and functions will be in this file

import pygame
import sys
import json
from queue import Queue
import tkinter.filedialog as f_dialog
from copy import deepcopy
import subprocess
import random

pygame.init()
pygame.font.init()

characters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

pretty_print_command = ["python", "-m", "json.tool", "--indent"]

screen = pygame.display.set_mode((800, 500))
clock = pygame.time.Clock()

pygame.display.set_caption("PyLevel Editor")

#Functions
def get_image(surf: pygame.Surface, x: int, y: int, width: int, height: int):
    new_surf = pygame.Surface((width, height))
    new_surf.set_colorkey((0, 0, 0))

    new_surf.blit(surf, (0, 0), (x, y, width, height))
    return new_surf

def blit_center(surf: pygame.Surface, other_surf: pygame.Surface, pos: list):
    width = other_surf.get_width()/2
    height = other_surf.get_height()/2
    surf.blit(other_surf, (pos[0]-width, pos[1]-height))

def perfect_outline(img, surf, loc, color, colorkey=(0,0,0)):
    img.set_colorkey(colorkey)
    mask = pygame.mask.from_surface(img)
    mask_surf = mask.to_surface(setcolor=color)
    mask_surf.set_colorkey((0,0,0))
    surf.blit(mask_surf,(loc[0]-1,loc[1]))
    surf.blit(mask_surf,(loc[0]+1,loc[1]))
    surf.blit(mask_surf,(loc[0],loc[1]-1))
    surf.blit(mask_surf,(loc[0],loc[1]+1))

#Classes
class Timer:
    def __init__(self, cooldown, callback=None):
        self.var = True
        self.time = None
        self.cooldown = cooldown*1000
        self.callback = callback

    def set_time(self):
        self.time = pygame.time.get_ticks()

    def set_var(self):
        self.var = False
    
    def set_callback(self, callback):
        self.callback = callback
    
    def set(self):
        self.set_time()
        self.set_var()

    def timed_out(self):
        return self.var

    def time_left(self):
        return (self.cooldown - (pygame.time.get_ticks() - self.time))/1000

    def reset(self):
        self.var = True
        self.time = None
    
    def set_cooldown(self, cooldown):
        self.cooldown = cooldown*1000

    def update(self):
        if self.var == False:
            current_time = pygame.time.get_ticks()

            if current_time - self.time >= self.cooldown:
                self.var = True
                if self.callback:
                    self.callback()

#UI stuff
class Button:
    def __init__(self, x, y, font, callback=None, image: pygame.Surface = None, text="", width=0, height=0, btn_color=(255, 255, 255), outline_on_hover=True, hover_color=(255, 255, 255), text_color=(0, 0, 0)):
        self.image = image
        self.text = text
        self.btn_color = btn_color
        self.text_color = text_color
        self.hover_color = hover_color
        self.outline_on_hover = outline_on_hover
        self.font = font
        self.clicked = False
        self.callback = callback
        self.hover = False

        if self.image != None:
            self.rect = self.image.get_rect(topleft=(x, y))
        else:
            self.rect = pygame.Rect(x, y, width, height)
            

    def draw(self, surf):
        if self.image != None:
            surf.blit(self.image, (self.rect.x, self.rect.y))

            if self.hover and self.outline_on_hover:
                pygame.draw.rect(surf, self.hover_color, self.rect, 2)

        else:
            pygame.draw.rect(surf, self.btn_color, self.rect)
            if self.hover and self.outline_on_hover:
                pygame.draw.rect(surf, self.hover_color, self.rect, 2)
        
        if self.font != None:
            text = self.font.render(self.text, False, self.text_color)
            blit_center(surf, text, self.rect.center)

    def update(self, mouse_pos):
        self.hover = False
        if self.rect.collidepoint(mouse_pos):
            self.hover = True

            if pygame.mouse.get_pressed()[0] and self.clicked == False:
                self.clicked = True

                if self.callback != None:
                    self.callback()
            
            if pygame.mouse.get_just_released()[0]:
                self.clicked = False


class TextInput:
    def __init__(self, pos, label, font, width, text_color=(255, 255, 255)):
        height = font.get_height()

        self.rect = pygame.Rect(pos[0], pos[1], width, height)
        self.text_surf = pygame.Surface(self.rect.size)
        self.text_surf.set_colorkey((1, 1, 1))
        self.text_color = text_color
        self.font = font
        self.label = label
        self.label_surf = self.font.render(label + ": ", False, text_color)
        self.text = ""
        self.backspacing = False
        self.backspace_time = 0
        self.selected = False
    
    def draw(self, surf):
        self.text_surf.fill((1, 1, 1))
        text = self.font.render(self.text, False, self.text_color)
        offset = max(0, (text.get_width()-self.rect.width) + 5)
        if offset > 0:
            offset += 13
        self.text_surf.blit(text, (4-offset, 1))
        surf.blit(self.label_surf, (self.rect.x-self.label_surf.get_width(), self.rect.y))
        surf.blit(self.text_surf, self.rect.topleft)
        color = (0, 0, 0)
        if self.selected:
            color = (200, 200, 200)
        pygame.draw.rect(surf, color, self.rect, 2)

    
    def update(self):
        if self.backspacing == True:
            if self.backspace_time > 30:
                self.text = self.text[0:len(self.text)-1]
            self.backspace_time += 1

    def handle_event(self, mouse_pos, event):

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(mouse_pos):
                    self.selected = True
                else:
                    self.selected = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                self.selected = False

            if self.selected:
                if event.key not in [pygame.K_RETURN, pygame.K_BACKSPACE, pygame.K_LCTRL, pygame.K_LALT]:
                    self.text += event.unicode
                
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[0:len(self.text)-1]
                    self.backspacing = True
        
        if event.type == pygame.KEYUP:
            if self.selected:
                if event.key == pygame.K_BACKSPACE:
                    self.backspace_time = 0
                    self.backspacing = False

class Object:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.name = ""
        self.properties = {}
    
    def to_data(self):
        data = {
            "rect": [self.rect.x, self.rect.y, self.rect.width, self.rect.height],
            "name": self.name,
            "properties": self.properties
        }
        return data
    
    @staticmethod
    def from_data(data):
        obj = Object(pygame.Rect(data["rect"]))
        obj.name = data["name"]
        obj.properties = data["properties"]
        
        return obj
    
    def draw(self, surf, scroll, zoom, font):
        pygame.draw.rect(surf, (0, 255, 0), (self.rect.x*zoom-scroll[0], self.rect.y*zoom-scroll[1], self.rect.width*zoom, self.rect.height*zoom), 2)
        blit_center(surf, font.render(self.name, False, (255, 255, 255), (0, 255, 0)), (self.rect.centerx*zoom-scroll[0], self.rect.y*zoom-30-scroll[1]))

class ObjectEditor:
    def __init__(self, font, x, y):
        self.pos = (x, y)
        self.font = font
        self.current_obj = None
        self.open = False
        self.surf = pygame.Surface((600, 400))
        self.surf.fill((100, 100, 100))
        self.ui_elements = [
            Button(550, 20, font, text="+", width=40, height=40, btn_color=(255, 0, 0), text_color=(255, 255, 255), callback=self.add_property), 
            TextInput([170, 20], "Name", font, 330),  
            TextInput([300, 340], "New Property", font, 180)
            ]
    
    def set_current_obj(self, obj: Object):
        self.current_obj = obj

        self.add_property(["Width", str(obj.rect.width)])
        self.add_property(["Height", str(obj.rect.height)])

        self.ui_elements[1].text = self.current_obj.name
        for prop in list(self.current_obj.properties.items()):
            self.add_property(prop)
    
    def add_property(self, _property=None):
        if _property == None:
            text_input = TextInput([170, 20+(len(self.ui_elements)-2)*self.ui_elements[1].rect.height*1.2], self.ui_elements[2].text, self.font, 330)
            self.ui_elements.append(text_input)
            self.ui_elements[2].text = ""

            self.current_obj.properties[text_input.label] = text_input.text

        else:
            text_input = TextInput([170, 20+(len(self.ui_elements)-2)*self.ui_elements[1].rect.height*1.2], _property[0], self.font, 330)
            text_input.text = _property[1]
            self.ui_elements.append(text_input)


    def reset_current_obj(self):
        self.current_obj = None
        self.ui_elements = self.ui_elements[0:3]

    def draw(self, surf):
        self.surf.fill((100, 100, 100))

        for elem in self.ui_elements:
            elem.draw(self.surf)

        surf.blit(self.surf, self.pos)
    
    def update(self, mouse_pos):
        if self.current_obj != None:
            self.current_obj.name = self.ui_elements[1].text

        for elem in self.ui_elements:
            if type(elem) == TextInput:
                elem.update()

                if self.current_obj != None:
                    if elem.label in self.current_obj.properties:
                        self.current_obj.properties[elem.label] = elem.text
                    
                    if elem.label == "Width":
                        try:
                            self.current_obj.rect.width = int(elem.text)
                        except:
                            pass

                    if elem.label == "Height":
                        try:
                            self.current_obj.rect.height = int(elem.text)
                        except:
                            pass

            if type(elem) == Button:
                elem.update(mouse_pos)

    def handle_events(self, event):
        for elem in self.ui_elements:
            if type(elem) == TextInput:
                pos = pygame.mouse.get_pos()
                elem.handle_event([pos[0]-self.pos[0], pos[1]-self.pos[1]], event)

class TileBtn(Button):
    def __init__(self, x, y, image, tile):
        super().__init__(x, y, None, image=image, hover_color=(255, 0, 0))
        self.tile = tile

class Level_Editor:
    def __init__(self):
        self.level = {"background": {}, "decor": {}, "tiles": {}, "foreground":{}}
        self.current_file = ""
        self.bounds = [0, 0, 10, 10] #left, top, right, bottom
        self.running = True
        self.tilesize = 16
        self.auto_tile_data = {}
        self.snap_to_grid = False

        # camera 
        self.scroll = [0, 0]
        self.scroll_speed = 10
        self.zoom = 1
        self.max_zoom = 3
        self.min_zoom = 0.25

        # Tile stuff
        self.tilesets = {}
        self.current_tile = 0
        self.current_tileset = ""
        self.tileset_index = 0
        self.layer_index = 2
        self.current_layer = list(self.level.keys())[self.layer_index]
        self.tile_buttons = {}
        self.tile_selection_mode = False

        #Key stuff
        self.ctrl = False

        # Mouse stuff
        self.clicking = False
        self.right_clicking = False
        self.clicked = False
        self.right_clicked = False

        #Text stuff
        self.font1 = pygame.font.SysFont("Arial", 25, True)
        self.font2 = pygame.font.SysFont("Arial", 35, True)

        # Feature
        self.selection_box = pygame.Rect(0, 0, 0, 0)
        self.selection_pos = [0, 0]
        self.selecting = False
        self.moving_selection = False
        self.placed_selection = False
        self.selection_surf = pygame.Surface((0, 0))
        self.rel_pos = [0, 0]
        self.selected_tiles = {}

        # Undo and redo
        self.logs = []
        self.undo_logs = []
        self.log_data = []
        self.undone = False
        self.redone = False

        # Copy and paste
        self.copy = {}

        #Object stuff
        self.objects = []
        self.object_mode = False
        self.obj_editor = ObjectEditor(self.font2, 100, 50)
        self.current_obj = None
        self.move_mode = False

        self.saved = False
        self.save_display_timer = Timer(0.8)

    def load_tileset(self, filename="", open_dialog=True):
        if open_dialog:
            filename = f_dialog.askopenfilename(filetypes=[("image", ".png"), ('json file', ".json")])
            if filename == "":
                return
        else:
            if filename == "":
                return

        if ".png" in filename:
            self.current_tile = 1
            tileset = filename.split('/')[-1].split(".")[0]
            self.tilesets[tileset] = {"type": "normal"}
            self.tile_buttons[tileset] = []
            image = pygame.image.load(filename).convert()
            image.set_colorkey((0, 0, 0))
            tile_id = 1
            row = 0
            for y in range(int(image.get_height()/self.tilesize)):
                for x in range(int(image.get_width()/self.tilesize)):
                    img = get_image(image, x*self.tilesize, y*self.tilesize, self.tilesize, self.tilesize)
                    self.tilesets[tileset][tile_id] = img

                    btn = TileBtn(80+(((tile_id-1)%10)*img.get_width()*2*1.2), 20+(row*img.get_height()*2*1.1), pygame.transform.scale(img, (img.get_width()*2, img.get_height()*2)), tile_id)
                    self.tile_buttons[tileset].append(btn)

                    if tile_id % 10 == 0:
                        row += 1

                    tile_id += 1
            self.current_tileset = tileset
            self.tilesets[tileset]["path"] = filename
        elif ".json" in filename:
            tileset = filename.split('/')[-1].split(".")[0]
            self.tilesets[tileset] = {"type": "custom"}
            self.tile_buttons[tileset] = []

            self.current_tileset = tileset

            with open(filename, "r") as file:
                data = json.load(file)
                file.close()
            
            image = pygame.image.load(data["path"]).convert()
            image.set_colorkey((0, 0, 0))
            
            tile_count = 0
            row = 0
            for tile in data:
                if tile != "path":
                    tile_id = tile
                    tile = data[tile_id]
                    tile_img = get_image(image, tile["x"], tile["y"], tile["width"], tile["height"])
                    self.tilesets[tileset][tile_id] = tile_img

                    btn = TileBtn(80+((tile_count%6)*tile_img.get_width()*2*1.2), 20+(row*tile_img.get_height()*2), pygame.transform.scale(tile_img, (tile_img.get_width()*2, tile_img.get_height()*2)), tile_id)
                    self.tile_buttons[tileset].append(btn)

                    if tile_count % 6 == 0 and tile_count != 0:
                        row += 1
                    
                    tile_count += 1
            
            self.current_tile = list(self.tilesets[tileset].keys())[1]
            self.tilesets[tileset]["path"] = filename

    def save(self, filename = ""):
        if filename == "":
            filename = f_dialog.asksaveasfilename(defaultextension=".lvl", filetypes=[("level file", ".lvl")])
            if filename == '':
                print("failed to save file")
                return
        
        self.current_file = filename

        level = {}

        level["tilesets"] = []
        for tileset in self.tilesets:
            level["tilesets"].append(self.tilesets[tileset]["path"])
        
        level["bounds"] = {"left": self.bounds[0], "right": self.bounds[2], "top": self.bounds[1], "bottom": self.bounds[3]}
        level["size"] = [self.bounds[2]-self.bounds[0], self.bounds[3]-self.bounds[1]]
        level["auto_tile_rules"] = self.auto_tile_data
        level["objects"] = []

        for obj in self.objects:
            level["objects"].append(obj.to_data())

        level["level"] = self.level.copy()

        with open(filename, "w") as file:
            json.dump(level, file)
            file.close()
        print("saved file!!")

        self.saved = True
        self.save_display_timer.set()
    
    def load_auto_tile_rules(self):
        filename = f_dialog.askopenfilename(filetypes=[("json file", ".json")])
        if filename == '':
            print("failed to load file")
            return

        with open(filename, "r") as file:
            data = json.load(file)
            file.close()
        
        self.auto_tile_data = data

        for tile in self.auto_tile_data:
            self.auto_tile_data[tile] = sorted(self.auto_tile_data[tile])

    
    def load(self):
        self.tilesets = {}
        filename = f_dialog.askopenfilename(filetypes=[("level file", ".lvl")])
        if filename == '':
            print("failed to load file")
            return

        self.current_file = filename
    
        self.scroll = [0, 0]
        self.objects = []
        self.objects = []
        self.object_mode = False
        self.current_obj = None
        self.move_mode = False

        
        with open(filename, "r") as file:
            data = json.load(file)
            file.close()

        self.bounds = [data["bounds"]["left"], data["bounds"]["top"], data["bounds"]["right"], data["bounds"]["bottom"]]

        for tileset in data["tilesets"]:
            self.load_tileset(tileset, open_dialog=False)
        
        self.level = data["level"]
        try:
            self.auto_tile_data = data["auto_tile_rules"]
        except:
            pass

        try:
            for obj in data["objects"]:
                self.objects.append(Object.from_data(obj))
        except:
            pass

        print("file loaded!!!")

    def flood_fill(self, x, y, new_tile):
        
        if x < self.bounds[0] or x > self.bounds[2] or y < self.bounds[1] or y > self.bounds[3]:
            return
        
        queue = Queue()
        
        if f"{x}/{y}" in self.level[self.current_layer]: # Flood filling already existing tiles
            old_tile = self.level[self.current_layer][f"{x}/{y}"][1]
            if old_tile == new_tile:
                return
            
            queue.put([x, y])
            
            while not queue.empty():
                _x, _y = queue.get()
                if _x < self.bounds[0] or _x > self.bounds[2] or _y < self.bounds[1] or _y > self.bounds[3]:
                    continue
                elif f"{_x}/{_y}" not in self.level[self.current_layer]:
                    continue
                elif self.level[self.current_layer][f"{_x}/{_y}"][1] != old_tile:
                    continue
                else:
                    self.level[self.current_layer][f"{_x}/{_y}"][1] = new_tile
                    self.log_data.append([self.current_layer, f"{_x}/{_y}", self.level[self.current_layer][f"{_x}/{_y}"]])
                    queue.put([_x-1, _y])
                    queue.put([_x+1, _y])
                    queue.put([_x, _y-1])
                    queue.put([_x, _y+1])

        else:
            # Empty tile so, we have to look for all tile ids not in self.level
            queue.put([x, y])

            while not queue.empty():
                _x, _y = queue.get()
                if _x < self.bounds[0] or _x > self.bounds[2] or _y < self.bounds[1] or _y > self.bounds[3]:
                    continue
                elif f"{_x}/{_y}" in self.level[self.current_layer]:
                    continue
                else:
                    self.level[self.current_layer][f"{_x}/{_y}"] = [self.current_tileset, new_tile, [_x, _y]]
                    self.log_data.append([self.current_layer, f"{_x}/{_y}", [self.current_tileset, new_tile, [_x, _y]]])
                    queue.put([_x-1, _y])
                    queue.put([_x+1, _y])
                    queue.put([_x, _y-1])
                    queue.put([_x, _y+1])
        
        self.log("placed", self.log_data)
        self.log_data.clear()

    def check_neighbours(self, pos):

        empty_neighbours = []

        if f"{pos[0]-1}/{pos[1]}" not in self.level[self.current_layer]:
            empty_neighbours.append([-1, 0])
        if f"{pos[0]+1}/{pos[1]}" not in self.level[self.current_layer]:
            empty_neighbours.append([1, 0])
        if f"{pos[0]}/{pos[1]-1}" not in self.level[self.current_layer]:
            empty_neighbours.append([0, -1])
        if f"{pos[0]}/{pos[1]+1}" not in self.level[self.current_layer]:
            empty_neighbours.append([0, 1])
        
        if len(empty_neighbours) == 0:
            if f"{pos[0]+1}/{pos[1]-1}" not in self.level[self.current_layer]:
                empty_neighbours.append([1, -1])
            if f"{pos[0]+1}/{pos[1]+1}" not in self.level[self.current_layer]:
                empty_neighbours.append([1, 1])
            if f"{pos[0]-1}/{pos[1]-1}" not in self.level[self.current_layer]:
                empty_neighbours.append([-1, -1])
            if f"{pos[0]-1}/{pos[1]+1}" not in self.level[self.current_layer]:
                empty_neighbours.append([-1, 1])
        
        return sorted(empty_neighbours)

    def auto_tile(self):

        for tile_id in self.level[self.current_layer]:
            # Check neighbours
            tile = self.level[self.current_layer][tile_id]
            if tile[0] == self.current_tileset:
                pos = tile[2]
                
                if tile[1] not in self.auto_tile_data["exclude"]:
                    check = self.check_neighbours(pos)
                    
                    for tile in self.auto_tile_data:
                        if check == self.auto_tile_data[str(tile)]:
                            self.level[self.current_layer][tile_id][1] = int(tile)
    
    def del_selection(self):
        tile_pos = [int(self.selection_box.x/self.tilesize), int(self.selection_box.y/self.tilesize)]
        for y in range(int(self.selection_box.height/self.tilesize)):
            for x in range(int(self.selection_box.width/self.tilesize)):
                tile_id = f"{tile_pos[0]+x}/{tile_pos[1]+y}"
                for layer in self.level:
                    if tile_id in self.level[layer]:
                        del self.level[layer][tile_id]
        
        self.selection_box.width = 0
        self.selection_box.height = 0
    
    def paste_selection(self, world_pos):
        pos = [int((world_pos[0]-self.rel_pos[0])/self.tilesize), int((world_pos[1]-self.rel_pos[1])/self.tilesize)]

        for layer in self.selected_tiles:
            for y in range(int(self.selection_surf.get_height()/self.tilesize)):
                for x in range(int(self.selection_surf.get_width()/self.tilesize)):
                    tile_id = f"{pos[0]+x}/{pos[1]+y}"
                    if f"{x}/{y}" in self.selected_tiles[layer]:
                        tile = self.selected_tiles[layer][f"{x}/{y}"]
                        tile[2] = [pos[0]+x, pos[1]+y]
                        self.level[layer][tile_id] = tile
        
        self.selected_tiles = {}
        self.moving_selection = False  
        self.clicking = False
    
    def copy_selection(self):
        pos = [int(self.selection_box.x/self.tilesize), int(self.selection_box.y/self.tilesize)]
        level = deepcopy(self.level)
        for layer in level:
            self.copy[layer] = {}
            for y in range(int(self.selection_box.height/self.tilesize)):
                for x in range(int(self.selection_box.width/self.tilesize)):
                    tile_id = f"{pos[0]+x}/{pos[1]+y}"
                    if tile_id in level[layer]:
                        tile = level[layer][tile_id]
                        self.copy[layer][f"{x}/{y}"] = tile
        
        self.selection_box.width = 0
        self.selection_box.height = 0

    def paste(self, pos):
        for layer in self.copy:
            for id in self.copy[layer]:
                id = id.split("/")
                x = int(id[0])
                y = int(id[1])
                tile_id = f"{pos[0]+x}/{pos[1]+y}"
                if f"{x}/{y}" in self.copy[layer]:
                    tile = deepcopy(self.copy[layer][f"{x}/{y}"])
                    tile[2] = [pos[0]+x, pos[1]+y]
                    self.level[layer][tile_id] = tile
    
    def log(self, log_type, data):
        log = {
            "type": log_type,
            "data": data
        }

        self.logs.append(json.dumps(log))
    
    def undo(self):
        if len(self.logs) > 0:
            l = self.logs.pop()
            self.undo_logs.append(l)
            log = json.loads(l)
        else:
            return

        log_type = log["type"]
        
        if log_type == "placed":
            for tile in log["data"]:
                if tile[1] in self.level[tile[0]]:
                    del self.level[tile[0]][tile[1]]
        elif log_type == "erased":
            for tile in log["data"]:
                self.level[tile[0]][tile[1]] = tile[2]
        
        self.undone = True
    
    def redo(self):
        if len(self.undo_logs) > 0:
            l = self.undo_logs.pop()
            self.logs.append(l)
            log = json.loads(l)
        else:
            return

        log_type = log["type"]
        
        if log_type == "placed":
            for tile in log["data"]:
                self.level[tile[0]][tile[1]] = tile[2]
        elif log_type == "erased":
            for tile in log["data"]:
                if tile[1] in self.level[tile[0]]:
                    del self.level[tile[0]][tile[1]]
        
        self.redone = True
    
    def run(self, surf):
        while self.running:
            surf.fill((127, 127, 127))
            clock.tick(60)

            self.clicked = False
            self.right_clicked = False

            m_pos = pygame.mouse.get_pos()
            world_pos = [(m_pos[0]+self.scroll[0])/self.zoom, (m_pos[1]+self.scroll[1])/self.zoom]

            # Updating level and level editor stuff
            if not self.obj_editor.open:
                if pygame.key.get_pressed()[pygame.K_a]:
                    self.scroll[0] -= self.scroll_speed
                if pygame.key.get_pressed()[pygame.K_d]:
                    self.scroll[0] += self.scroll_speed
                if pygame.key.get_pressed()[pygame.K_w]:
                    self.scroll[1] -= self.scroll_speed
                if pygame.key.get_pressed()[pygame.K_s]:
                    self.scroll[1] += self.scroll_speed
            
            tile_pos = [((m_pos[0]+self.scroll[0])/self.zoom)/self.tilesize, ((m_pos[1]+self.scroll[1])/self.zoom)/self.tilesize]

            if tile_pos[0] < 0:
                tile_pos[0] -= 1
            if tile_pos[1] < 0:
                tile_pos[1] -= 1

            tile_pos = [int(tile_pos[0]), int(tile_pos[1])]

            tile_id = f"{tile_pos[0]}/{tile_pos[1]}"

            if self.current_tileset != "":
                if self.clicking and not self.moving_selection and not self.object_mode and not self.tile_selection_mode:
                    if self.current_tile in self.tilesets[self.current_tileset]:
                        if tile_id not in self.level:
                            self.level[self.current_layer][tile_id] = []

                        if tile_pos[0] < self.bounds[0]:
                            self.bounds[0] = tile_pos[0]
                        elif tile_pos[0] > self.bounds[2]:
                            self.bounds[2] = tile_pos[0]

                        if tile_pos[1] < self.bounds[1]:
                            self.bounds[1] = tile_pos[1]
                        elif tile_pos[1] > self.bounds[3]:
                            self.bounds[3] = tile_pos[1]

                        tile = [self.current_tileset, self.current_tile, tile_pos]
                        self.level[self.current_layer][tile_id] = tile

                        if self.undone or self.redone:
                            self.undo_logs.clear()
                        
                        self.undone = False
                        self.redone = False

                        self.log_data.append([self.current_layer, tile_id, tile])
                
                if self.right_clicking and not self.moving_selection and not self.object_mode and not self.tile_selection_mode:

                    if self.undone or self.redone:
                        self.undo_logs.clear()
                        
                    self.undone = False
                    self.redone = False

                    if tile_id in self.level[self.current_layer]:
                        self.log_data.append([self.current_layer, tile_id, self.level[self.current_layer][tile_id]])

                        del self.level[self.current_layer][tile_id]


            
            # Event handling
            for event in pygame.event.get():
                
                if self.obj_editor.open:
                    self.obj_editor.handle_events(event)

                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = True
                    
                    if event.key == pygame.K_ESCAPE:
                        self.obj_editor.open = False
                        self.obj_editor.reset_current_obj()
                    
                    if event.key == pygame.K_F5: # quicksave
                        self.save(self.current_file)
                    
                    if event.key == pygame.K_q:
                        if not self.object_mode:
                            if not self.ctrl:
                                if len(self.auto_tile_data) > 0:
                                    self.auto_tile()
                            else:
                                self.load_auto_tile_rules()
                    
                    if event.key == pygame.K_t:
                        if not self.ctrl and not self.object_mode:
                            self.tile_selection_mode = not self.tile_selection_mode
                    
                    if self.ctrl:
                        if event.key == pygame.K_s:
                            self.save()
                        if event.key == pygame.K_l:
                            self.load()
                        if event.key == pygame.K_t:
                            self.load_tileset()
                        if event.key == pygame.K_f:
                            self.flood_fill(tile_pos[0], tile_pos[1], self.current_tile)
                        if event.key == pygame.K_c:
                            self.copy_selection()
                        if event.key == pygame.K_v:
                            self.paste(tile_pos)
                        if event.key == pygame.K_z:
                            self.undo()
                        if event.key == pygame.K_y:
                            self.redo()
                        if event.key == pygame.K_EQUALS:
                            if not (0 < self.zoom < 1):
                                self.zoom += 1
                                self.zoom = min(self.max_zoom, self.zoom)
                            else:
                                if self.zoom == self.min_zoom:
                                    self.zoom = 0.5
                                elif self.zoom == 0.5:
                                    self.zoom = 1
                            
                            self.scroll[0] *= self.zoom
                            self.scroll[1] *= self.zoom

                        if event.key == pygame.K_MINUS:
                            self.zoom -= 1
                            if self.zoom == 0:
                                self.zoom = 0.5
                            elif self.zoom < 0:
                                self.zoom = self.min_zoom
                            
                            self.scroll[0] /= self.zoom
                            self.scroll[1] /= self.zoom
                    
                    if event.key == pygame.K_LEFT:
                        if len(self.tilesets) > 0:
                            self.tileset_index -= 1
                            self.tileset_index = max(0, self.tileset_index) 
                            self.current_tileset = list(self.tilesets.keys())[self.tileset_index]
                            if self.tilesets[self.current_tileset]["type"] == "normal":
                                self.current_tile = 1
                            else:
                                self.current_tile = list(self.tilesets[self.current_tileset].keys())[1]

                    if event.key == pygame.K_RIGHT:
                        if len(self.tilesets) > 0:
                            tilesets = list(self.tilesets.keys())
                            self.tileset_index += 1
                            self.tileset_index = min(self.tileset_index, len(tilesets)-1) 
                            self.current_tileset = tilesets[self.tileset_index]
                            if self.tilesets[self.current_tileset]["type"] == "normal":
                                self.current_tile = 1
                            else:
                                self.current_tile = list(self.tilesets[self.current_tileset].keys())[1]
                    
                    if event.key == pygame.K_UP:
                        self.layer_index += 1
                        self.layer_index = min(len(self.level)-1, self.layer_index)
                        self.current_layer = list(self.level.keys())[self.layer_index]
                    
                    if event.key == pygame.K_DOWN:
                        self.layer_index -= 1
                        self.layer_index = max(0, self.layer_index)
                        self.current_layer = list(self.level.keys())[self.layer_index]
                    
                    if event.key == pygame.K_LSHIFT:
                        self.object_mode = not self.object_mode
                        self.move_mode = False
                    
                    if event.key == pygame.K_o:
                        if self.object_mode:
                            self.objects.append(Object(deepcopy(self.selection_box)))
                            self.selection_box.width = 0
                            self.selection_box.height = 0
                    
                    if event.key == pygame.K_m:
                        if self.object_mode and self.ctrl:
                            self.move_mode = not self.move_mode
                            self.obj_editor.open = False
                    
                    if event.key == pygame.K_DELETE:
                        self.del_selection()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        self.clicked = True
                        if self.moving_selection:
                            self.paste_selection(world_pos)

                    if event.button == 2:
                        self.selecting = True
                        self.selection_pos = tile_pos.copy()
                        self.selection_box.x = tile_pos[0]*self.tilesize
                        self.selection_box.y = tile_pos[1]*self.tilesize
                    
                    if event.button == 3:
                        self.right_clicking = True
                        self.right_clicked = True

                
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                        self.clicked = False

                        self.log("placed", self.log_data)
                        self.log_data.clear()

                    if event.button == 2:
                        self.selecting = False
                    
                    if event.button == 3:
                        self.right_clicking = False
                        self.right_clicked = False

                        self.log("erased", self.log_data)
                        self.log_data.clear()

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LCTRL:
                        self.ctrl = False
                
                if event.type == pygame.MOUSEWHEEL:
                    if event.y == -1:
                        if self.tilesets[self.current_tileset]["type"] == "normal":
                            tile_ids = list(self.tilesets[self.current_tileset].keys())
                            tile_ids = tile_ids[1:len(tile_ids)-1]
                            self.current_tile += 1
                            self.current_tile = min(self.current_tile, max(tile_ids))
                        elif self.tilesets[self.current_tileset]["type"] == "custom":
                            tile_ids = list(self.tilesets[self.current_tileset].keys())
                            tile_ids = tile_ids[1:len(tile_ids)-1]
                            index = tile_ids.index(self.current_tile) + 1
                            index = min(len(tile_ids)-1, index)
                            self.current_tile = tile_ids[index]

                    if event.y == 1:
                        if self.tilesets[self.current_tileset]["type"] == "normal":
                            self.current_tile -= 1
                            self.current_tile = max(1, self.current_tile)
                        elif self.tilesets[self.current_tileset]["type"] == "custom":
                            tile_ids = list(self.tilesets[self.current_tileset].keys())
                            tile_ids = tile_ids[1:len(tile_ids)-1]
                            index = tile_ids.index(self.current_tile) - 1
                            index = max(0, index)
                            self.current_tile = tile_ids[index]



            # Rendering
            for layer in self.level:
                for y in range(int((-self.tilesize*2 + self.scroll[1])/self.tilesize/self.zoom), int((surf.get_height()+self.tilesize + self.scroll[1])/self.tilesize/self.zoom)):
                    for x in range(int((-self.tilesize*2 + self.scroll[0])/self.tilesize/self.zoom), int((surf.get_width()+self.tilesize + self.scroll[0])/self.tilesize/self.zoom)):
                        tile_id = f"{x}/{y}"
                        if tile_id in self.level[layer]:
                            tile = self.level[layer][tile_id]
                            if (-(self.tilesize*self.zoom)*2 < tile[2][0]*self.tilesize*self.zoom-self.scroll[0] < surf.get_width()+self.tilesize*2) and (-(self.tilesize*self.zoom)*2 < tile[2][1]*self.tilesize*self.zoom-self.scroll[1] < surf.get_height()+self.tilesize*2):
                                img = self.tilesets[tile[0]][tile[1]].copy()
                                surf.blit(pygame.transform.scale(img, (img.get_width()*self.zoom, img.get_height()*self.zoom)), (tile[2][0]*self.tilesize*self.zoom-self.scroll[0], tile[2][1]*self.tilesize*self.zoom-self.scroll[1]))

            if (self.selecting and not self.moving_selection) or (self.selecting and self.object_mode):
                width = tile_pos[0] - self.selection_pos[0] + 1
                height = tile_pos[1] - self.selection_pos[1] + 1

                if width < 0:
                    self.selection_box.x = (self.selection_pos[0]-abs(width))*self.tilesize
                else:
                    self.selection_box.x = self.selection_pos[0]*self.tilesize
                if height < 0:
                    self.selection_box.y = (self.selection_pos[1]-abs(height))*self.tilesize
                else:
                    self.selection_box.y = self.selection_pos[1] * self.tilesize

                self.selection_box.width = abs(width)*self.tilesize
                self.selection_box.height = abs(height)*self.tilesize

            color = (255, 0, 0)
            if self.object_mode:
                color = (0, 255, 0)
            pygame.draw.rect(surf, color, (self.selection_box.x*self.zoom-self.scroll[0], self.selection_box.y*self.zoom-self.scroll[1], self.selection_box.width*self.zoom, self.selection_box.height*self.zoom), 1)

            if self.selection_box.collidepoint(world_pos) and pygame.mouse.get_pressed()[0] and not self.moving_selection and not self.object_mode:
                self.moving_selection = True
                self.selection_pos = world_pos
                self.selection_surf = pygame.Surface((self.selection_box.width, self.selection_box.height))
                self.selection_surf.set_colorkey((0, 0, 0))
                self.rel_pos = [world_pos[0]-self.selection_box.x, world_pos[1]-self.selection_box.y]

                # Render tiles in this surface
                pos = [int(self.selection_box.x/self.tilesize), int(self.selection_box.y/self.tilesize)]
                for layer in self.level:
                    self.selected_tiles[layer] = {}
                    for y in range(int(self.selection_box.height/self.tilesize)):
                        for x in range(int(self.selection_box.width/self.tilesize)):
                            tile_id = f"{pos[0]+x}/{pos[1]+y}"
                            if tile_id in self.level[layer]:
                                tile = self.level[layer][tile_id]
                                self.selected_tiles[layer][f"{x}/{y}"] = tile
                                self.selection_surf.blit(self.tilesets[tile[0]][tile[1]], (x*self.tilesize, y*self.tilesize))
                self.del_selection()

            
            if self.move_mode and self.current_obj != None:
                if self.ctrl:
                    self.snap_to_grid = True
                else:
                    self.snap_to_grid = False

                if not self.snap_to_grid:
                    self.current_obj.rect.x = world_pos[0]
                    self.current_obj.rect.y = world_pos[1]
                else:
                    self.current_obj.rect.x = int(world_pos[0]/self.tilesize)*self.tilesize
                    self.current_obj.rect.y = int(world_pos[1]/self.tilesize)*self.tilesize

            for i, obj in sorted(enumerate(self.objects), reverse=True):
                obj.draw(surf, self.scroll, self.zoom, self.font1)
                
                if obj.rect.collidepoint(world_pos) and self.obj_editor.open == False:
                    if self.right_clicked and (self.object_mode and not self.move_mode):
                        self.objects.pop(i)
                        continue
                    if self.clicked:
                        if not self.move_mode and self.object_mode:
                            self.obj_editor.open = True
                            self.obj_editor.set_current_obj(obj)
                        else:
                            if self.current_obj == None:
                                self.current_obj = obj
                            else:
                                self.current_obj = None


            if self.moving_selection:
                surf.blit(self.selection_surf, (int((world_pos[0]-self.rel_pos[0])/self.tilesize)*self.tilesize-self.scroll[0], int((world_pos[1]-self.rel_pos[1])/self.tilesize)*self.tilesize-self.scroll[1]))
                pygame.draw.rect(surf, (255, 0, 0), (int((world_pos[0]-self.rel_pos[0])/self.tilesize)*self.tilesize-self.scroll[0], int((world_pos[1]-self.rel_pos[1])/self.tilesize)*self.tilesize-self.scroll[1], self.selection_surf.get_width(), self.selection_surf.get_height()), 1)


            if self.selection_box.width != 0:
                text = self.font1.render(f"Selection box( pos: {self.selection_box.topleft}, width: {self.selection_box.width}, height: {self.selection_box.height})", False, (255, 255, 255))
                surf.blit(text, (surf.get_width()-text.get_width()-20, surf.get_height()-text.get_height()-10))
            
            if self.saved:
                filename = self.current_file.split("/")[-1]
                text = self.font1.render(f"{filename} was saved!!", False, (255, 255, 255))
                surf.blit(text, (surf.get_width()-text.get_width()-20, 20))

            try:
                if self.current_tileset != "":
                    if not self.object_mode:
                        if self.tile_selection_mode:
                            for btn in self.tile_buttons[self.current_tileset]:
                                btn.update(m_pos)
                                btn.draw(surf)

                                if btn.clicked:
                                    self.current_tile = btn.tile
                                

                        img = self.tilesets[self.current_tileset][self.current_tile].copy()
                        surf.blit(pygame.transform.scale(img, (img.get_width()*3, img.get_height()*3)), (20, 20))

                if not self.object_mode:
                    if self.current_tileset != "":
                        text = f"Tileset: {self.current_tileset} | Tile: {self.current_tile}\nLayer: {self.current_layer} | Zoom: {self.zoom}\nTile pos: x: {tile_pos[0]}, y: {tile_pos[1]}"
                    else:
                        text = " "
                else:
                    if not self.move_mode:
                        text = "Object Mode"
                    else:
                        text = "Move Object Mode"
                
                info = self.font1.render(text, False, (255, 255, 255))
                surf.blit(info, (20, surf.get_height()-info.get_height()*1.2))
            except Exception as e:
                print(e)
            
            if self.obj_editor.open:
                self.obj_editor.update([m_pos[0]-100, m_pos[1]-50])
                self.obj_editor.draw(surf)
            
            self.save_display_timer.update()

            if self.save_display_timer.timed_out():
                self.saved = False

            pygame.display.update()
        

level_editor = Level_Editor()
level_editor.run(screen)

pygame.quit()


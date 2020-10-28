import transformations as tr
import basic_shapes as bs
import scene_graph as sg
import easy_shaders as es

import numpy as np
import glfw
import sys
from typing import Union
from typing import List
import csv

from OpenGL.GL import *


#CONTROLADOR

class Controller(object):

    model: Union['Mono', None]  
    platforms: Union['platformCreator', None]

    def __init__(self):
        self.model = None  
        self.platforms = None
        self.jump = False
        self.up = True
        self.create = True
        self.in_platform = False
        self.win = False
        self.start = False

    def set_model(self, m):
        self.model = m

    def set_platforms(self, e):
        self.platforms = e

    def on_key(self, window, key, scancode, action, mods):
        if action != glfw.PRESS:
            return

        if key == glfw.KEY_ESCAPE:
            sys.exit()

        if key == glfw.KEY_W:  
            self.jump = not self.jump

controlador = Controller()

#MODELOS

#monito
class Mono(object):
    
    def __init__(self):
        #figuras basicas
        gpu_Brown_Circle = es.toGPUShape(bs.createTextureQuad('monito.PNG'), GL_REPEAT, GL_NEAREST)
        gpu_armslegs_Quad = es.toGPUShape(bs.createColorQuad(0.6, 0.3, 0))

        # Piernas
        leg = sg.SceneGraphNode('leg') 
        leg.transform = tr.matmul([ 
           tr.scale(0.2, 0.3, 1),
          ])  
        leg.childs += [gpu_armslegs_Quad]

        # Izquierda
        leg_izq = sg.SceneGraphNode('legLeft')
        leg_izq.transform = tr.matmul([
            tr.translate(-0.1, -0.5, 0),
            tr.scale(0.5, 1, 1),
          ])  
        leg_izq.childs += [leg]

        # Derecha
        leg_der = sg.SceneGraphNode('legRight')
        leg_der.transform = tr.matmul([
            tr.translate(0.1, -0.5, 0),
            tr.scale(0.5, 1, 1),
          ])  
        leg_der.childs += [leg]

        # Brazos 
        arm = sg.SceneGraphNode('arm')  # pierna generica
        arm.transform = tr.matmul([
            tr.translate(0, 0, 0),
            tr.scale(0.4, 0.1, 1)
            ])
        arm.childs += [gpu_armslegs_Quad]

        # Izquierdo
        arm_izq = sg.SceneGraphNode('armLeft')
        arm_izq.transform = tr.matmul([
            tr.translate(-0.3, -0.1, 0),
            tr.rotationZ(30 * np.pi / 180)
            ]) 
        arm_izq.childs += [arm]

        # Derecho
        arm_der = sg.SceneGraphNode('armRight')
        arm_der.transform = tr.matmul([
            tr.translate(0.3, -0.1, 0),
            tr.rotationZ(-30 * np.pi / 180)
            ])
        arm_der.childs += [arm]

        # Usan shader de color
        armslegs = sg.SceneGraphNode('armslegs')
        armslegs.transform = tr.matmul([ tr.translate(0, -0.5, 0),tr.scale(0.4, 0.4, 0)])
        armslegs.childs += [leg_izq, leg_der, arm_izq, arm_der]

        armslegstr = sg.SceneGraphNode('armslegstr')
        armslegstr.childs += [armslegs]
        
        # Usa shader de texturas
        body = sg.SceneGraphNode('body')
        body.transform = tr.matmul([ 
            tr.scale(0.6, 0.95, 1),
            tr.translate(0.06, -0.54, 0)
          ])
        body.childs += [gpu_Brown_Circle]

        bodytr =  sg.SceneGraphNode('bodytr')
        bodytr.childs += [body]

        mono = sg.SceneGraphNode('mono')
        mono.childs += [bodytr, armslegstr]

        self.model = mono
        self.pos_x = 0
        self.pos_y = 0
        self.pos = 0  

    def draw(self, pipeline, pipeline1):

        # Se dibujan los brazos y las piernas con un color
        sg.findNode(self.model, 'armslegstr').transform = tr.translate(0.7 * self.pos_x, self.pos_y, 0)
        glUseProgram(pipeline.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "transform"), 1, GL_TRUE,
                           tr.matmul([
                               tr.translate(0, 0, 0),
                               tr.scale(0, 0, 0)]))
        sg.drawSceneGraphNode(sg.findNode(self.model, 'armslegstr'), pipeline, 'transform')

        # Se dibuja el resto del cuerpo con una textura
        sg.findNode(self.model, 'bodytr').transform = tr.translate(0.7 * self.pos_x, self.pos_y, 0)
        glUseProgram(pipeline1.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(pipeline1.shaderProgram, "transform"), 1, GL_TRUE,
                           tr.matmul([
                               tr.translate(0, 0, 0),
                               tr.scale(0, 0, 0)]))
    
        sg.drawSceneGraphNode(sg.findNode(self.model, 'bodytr'), pipeline1, 'transform')


    def move_left(self, dt):
        self.pos_x -= dt

    def move_right(self, dt):
        self.pos_x += dt

    def move_up(self, dt):
        self.pos_y += dt
    
    # Funcion para que mueva los brazos al saltar
    def moveArms(self, ang, tras):
        arm1 = sg.findNode(self.model, 'armRight')
        arm1.transform =   tr.matmul([
            tr.translate(0.3, tras, 0),
            tr.rotationZ(-30 * np.pi / 180), tr.rotationZ(-ang * np.pi / 180), 
            ])
        arm2 = sg.findNode(self.model, 'armLeft')
        arm2.transform =   tr.matmul([
            tr.translate(-0.3, tras, 0),
            tr.rotationZ(30 * np.pi / 180), tr.rotationZ(ang * np.pi / 180), 
            ])
            
    # Funcion para que caiga en las plataformas
    def collide(self, platforms: 'platformCreator'):
        for e in platforms.platforms:
            if (e.pos_y - (self.pos_y - 0.75) <= 0.05) and (e.pos_y - (self.pos_y - 0.75) >= -0.05) and (e.pos_x == self.pos):
                controlador.jump = False
                controlador.up = True
                controlador.in_platform = True
    
    # Funcion para que no pueda atravesar las plataformas
    def roof(self):
        for e in platforms.platforms:
            if (e.pos_y - (self.pos_y - 0.3) <= 0.05) and (e.pos_y - (self.pos_y - 0.3) >= -0.05) and (e.pos_x == self.pos):
                controlador.jump = True
                controlador.up = False
                controlador.in_platform = False
    
    # Funcion para que muera cuando se cae
    def die(self, pipeline):
        if self.pos_y <= -1:
            fondo = es.toGPUShape(bs.createTextureQuad('gameover.jpg'), GL_REPEAT, GL_NEAREST)
            glUseProgram(pipeline.shaderProgram)
            glUniformMatrix4fv(glGetUniformLocation(pipeline.shaderProgram, "transform"), 1, GL_TRUE, tr.matmul([
                tr.translate(0, 0, 0),
                tr.scale(2, 2, 1.0)]))
            pipeline.drawShape(fondo)

    # Funcion para cuando llega a la ultima plataforma
    def win(self, platforms: 'platformCreator', pipeline1):
        i = len(platforms.platforms) - 1
        if (platforms.platforms[i].pos_y - (self.pos_y - 0.8) <= 0.05) and (platforms.platforms[i].pos_y - (self.pos_y - 0.8) >= -0.05) and (platforms.platforms[i].pos_x == self.pos):
            glClearColor(0, 0.8, 0, 1.0)
            self.moveArms(100, 0.2)
            controlador.win = True
            
             
        
        
#plataforma
class Platform(object):
    
    # Clase que crea una plataforma en una columna y una fila especifica
    def __init__(self, column, row):
        gpu_platform = es.toGPUShape(bs.createTextureQuad('plataforma.png'), GL_REPEAT, GL_NEAREST)


        platform = sg.SceneGraphNode('platform')
        platform.transform = tr.scale(0.45, 0.2, 1)
        platform.childs += [gpu_platform]

        platform_tr = sg.SceneGraphNode('platformTR')
        platform_tr.childs += [platform]

        self.pos_y = row
        self.pos_x = column
        self.model = platform_tr

    def draw(self, pipeline):
        self.model.transform = tr.translate(0.7 * self.pos_x, self.pos_y, 0)
        glUseProgram(pipeline.shaderProgram)
        sg.drawSceneGraphNode(self.model, pipeline, "transform")

    def update(self, dt):
        self.pos_y -= 0.7*dt

#lista de plataformas
class platformCreator(object):
    platforms: List['Platform']

    def __init__(self):
        self.platforms = []
        self.on = True
    
    # Se crea lista de plataformas leyendo el archivo
    def create_platform(self):
        with open('structure.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')

            line_count = 0
            for row in csv_reader:
                if row[0] == '1':
                    self.platforms.append(Platform(-1, line_count))
                    
                if row[1] == '1':
                    self.platforms.append(Platform(0, line_count))
                
                if row[2] == '1':
                    self.platforms.append(Platform(1, line_count))
            
                line_count += 1
        
            controlador.create = False
        
    # Se dibujan todas las plataformas de la lista
    def draw(self, pipeline):
        for k in self.platforms:
            k.draw(pipeline)

    def update(self, dt):
        for k in self.platforms:
            k.update(dt)

#banana
class Banana(object):

    def __init__(self):
        gpu_banana = es.toGPUShape(bs.createTextureQuad('banana1.png'), GL_REPEAT, GL_NEAREST)

        banana = sg.SceneGraphNode('banana')
        banana.transform = tr.scale(0.2, 0.2, 1)
        banana.childs += [gpu_banana]

        banana_tr = sg.SceneGraphNode('bananaTR')
        banana_tr.childs += [banana]

        self.pos_y = 0
        self.pos_x = 0
        self.model = banana_tr
    
    # Solo se dibuja si esta en la ultima plataforma de la lista
    def draw(self, pipeline, platforms: 'platformCreator'):
        i = len(platforms.platforms) - 1     
        self.pos_y = platforms.platforms[i].pos_y + 0.1
        self.pos_x = platforms.platforms[i].pos_x
        self.model.transform = tr.translate(0.7 * self.pos_x, self.pos_y, 0)
        glUseProgram(pipeline.shaderProgram)
        sg.drawSceneGraphNode(self.model, pipeline, "transform")


#VISTA

if __name__ == '__main__':

    # Initialize glfw
    if not glfw.init():
        sys.exit()

    width = 800
    height = 800

    window = glfw.create_window(width, height, 'Mono saltarin', None, None)

    if not window:
        glfw.terminate()
        sys.exit()

    glfw.make_context_current(window)

    glfw.set_key_callback(window, controlador.on_key)

    # Assembling the shader programs (pipeline) with both shaders
    pipeline = es.SimpleTransformShaderProgram()
    pipeline1 = es.SimpleTextureTransformShaderProgram()

    # Setting up the clear screen color
    glClearColor(0.85, 0.85, 0.85, 1.0)
    
    # Transperencies
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Our shapes here are always fully painted
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # HACEMOS LOS OBJETOS
    fondo1 = es.toGPUShape(bs.createTextureQuad('fondo 2.png'), GL_REPEAT, GL_NEAREST)

    monofinal = Mono()

    platforms = platformCreator()

    banana = Banana()

    controlador.set_platforms(platforms)

    t0 = 0
    posicion = monofinal.pos_y
    
    while not glfw.window_should_close(window):  
         
        # Using GLFW to check for input events
        glfw.poll_events() 

        # Clearing the screen in both, color and depth
        glClear(GL_COLOR_BUFFER_BIT)
        
        # Se crean las plataformas hasta que se termina de leer el archivo
        if (controlador.create):
            platforms.create_platform()

        # Se dibuja el fondo que se mueve con las plataformas
        glUseProgram(pipeline1.shaderProgram)
        glUniformMatrix4fv(glGetUniformLocation(pipeline1.shaderProgram, "transform"), 1, GL_TRUE, tr.matmul([
                tr.translate(0,4+ platforms.platforms[0].pos_y, 0),
                tr.scale(2, 10, 1.0)]))
        pipeline1.drawShape(fondo1)

        # En que posicion de las plataformas esta el monito
        if monofinal.pos_x < -0.6:
            monofinal.pos = -1
        elif monofinal.pos_x > 0.6:
            monofinal.pos = 1
        else:
            if monofinal.pos_x > -0.4 and monofinal.pos_x < 0.4:
                monofinal.pos = 0
            #else:
             #   monofinal.pos =0.1
      
        
        # Deja de crear plataformas cuando termina el archivo


        ti = glfw.get_time()
        dt = ti - t0
        t0 = ti

        if controlador.jump == False and controlador.start == True:
            posicion = monofinal.pos_y
            if (monofinal.pos_x - monofinal.pos) < -0.25 or (monofinal.pos_x - monofinal.pos) > 0.25:
                controlador.jump = True
                controlador.up = False

        if controlador.jump == True:
            controlador.start = True
            controlador.in_platform = False
            if (controlador.up):
                platforms.update(dt) 
                monofinal.roof()
                if monofinal.pos_y < 0.7 + posicion:
                    monofinal.move_up(dt)
                    monofinal.moveArms(100, 0.1)
                else:
                    controlador.up = not controlador.up
            else:
                monofinal.moveArms(10, -0.1)
                monofinal.collide(platforms)
                monofinal.move_up(-dt)

                if not (controlador.in_platform):
                    if platforms.platforms[0].pos_y <= 0: 

                        if monofinal.pos_y <= 0.3:
                            monofinal.move_up(dt)
                            platforms.update(-dt)

                elif monofinal.pos_y <= 0:
                            controlador.jump = not controlador.jump 
                            controlador.up = not controlador.up
        

        if (controlador.in_platform):
            if monofinal.pos_y > 0.3:
                monofinal.move_up(-0.35 * dt)
                platforms.update(0.5 * dt)
     
        if (glfw.get_key(window, glfw.KEY_W) == glfw.PRESS):
            if not(controlador.jump):
                controlador.jump = not controlador.jump
            
        if (glfw.get_key(window, glfw.KEY_A) == glfw.PRESS):
            monofinal.move_left(2*dt)

        if (glfw.get_key(window, glfw.KEY_D) == glfw.PRESS):
            monofinal.move_right(2*dt)

        # Dibuja objetos    

        platforms.draw(pipeline1)
      
        monofinal.draw(pipeline, pipeline1)

        banana.draw(pipeline1, platforms)

        # Funciones para cuando pierde o gana
        
        monofinal.die(pipeline1)
        if controlador.win == False:
            monofinal.win(platforms, pipeline1)
        
        if controlador.win == True:
            arm1 = sg.findNode(monofinal.model, 'armRight')
            arm1.transform =   tr.matmul([
               tr.translate(-0.2, 0, 0),
               tr.rotationZ(-30 * np.pi / 180), tr.rotationZ(0.5 * np.sin( 7*ti)),
               tr.translate(-0.1, 0, 0) 
               ])
            arm2 = sg.findNode(monofinal.model, 'armLeft')
            arm2.transform =   tr.matmul([
                tr.translate(0.2, 0, 0),
                tr.rotationZ(30 * np.pi / 180), tr.rotationZ(-0.5 * np.sin(7*ti)),
                tr.translate(0.1, 0, 0) 
                ])
        # Once the render is done, buffers are swapped, showing only the complete scene.
        glfw.swap_buffers(window)

    glfw.terminate()
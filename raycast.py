import pygame
import math
from collections import deque

pygame.init()
clock = pygame.time.Clock()

RAYS = 500
WALL_HEIGHT = 7500.0
LINE_OF_SIGHT_RADIUS = 450.0

def cross_product(a,b,c):
    """cross product given 3 points"""
    return (a[0] - c[0])*(b[1] - c[1]) - (a[1] - c[1]) * (b[0] - c[0])

def line_line_intersection(a,b,c,d):
    """given points from a to b and c to d, calculate if line segments intersect"""
    sign1 = cross_product(c, d, a)
    sign2 = cross_product(c, d, b)
    
    if sign1 * sign2 < 0: #signs are differnt if lines intersect
        sign3 = cross_product(c, b, a)
        sign1 = sign3 + sign2 - sign1
        
        if sign1 * sign3 <= 0:
            return True
 
class Vector:
    
    __slots__ = ('start_pos', 'end_pos', 'x_component', 'y_component', 'leng', 'rot_x_comp', 'rot_y_comp', 'unit_x', 'unit_y')
   
    def __init__(self,start_pos, end_pos):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.x_component = end_pos[0] - start_pos[0]
        self.y_component = end_pos[1] - start_pos[1]
        self.leng = LINE_OF_SIGHT_RADIUS #default to avoid unneeded calculation
        self.rot_x_comp = self.x_component
        self.rot_y_comp = self.y_component
   
    def vect_direction(self, start_pos, end_pos):
        """calculate vector components"""
        self.tmp1 = end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]
        return self.tmp1
                
    def vect_length(self):
        """calculate vector length"""
        self.leng =  math.hypot(self.x_component, self.y_component)
       
    def vect_rotate(self,angle):
        """rotate vector by angle"""
        self.rot_x_comp = math.cos(angle)*self.x_component - math.sin(angle) * self.y_component + self.start_pos[0]
        self.rot_y_comp = math.sin(angle)*self.x_component + math.cos(angle) * self.y_component + self.start_pos[1]
            
    def los_vect_rotate(self,angle):
        """rotate vector by angle"""
        #Stripped from component thus making calculations cheaper since y_component equals 0
        self.rot_x_comp = math.cos(angle)*self.x_component + self.start_pos[0]
        self.rot_y_comp = math.sin(angle)*self.x_component + self.start_pos[1]
    
    def cross_product(self, end):
        """calculate cross product of vector"""
        self.tmp_b = self.vect_direction(self.start_pos, end)
        return self.rot_x_comp * self.tmp_b[1] - self.rot_y_comp * self.tmp_b[0]
   
    def unit_vect(self):
        """calculate unit vector"""
        self.unit_x = (self.rot_x_comp - self.start_pos[0])/self.leng
        self.unit_y = (self.rot_y_comp - self.start_pos[1])/self.leng
 
class Map:
                    #color, start_pos, end_pos
    line_1 = (255, 255, 0), (100,125), (50, 250)
    line_2 = (255, 255, 0), (50,250), (100, 400)
    line_3 = (255, 0, 255), (30,400), (250, 450)
    line_4 = (255, 0, 255), (250,450), (400, 500)
    line_5 = (0, 255, 255), (400,30), (320, 250)
    line_6 = (0, 255, 255), (320,250), (250, 500)
   
    all_objects = set((line_1,line_6,line_4,line_5,line_3,line_2)) #set for fast random access
    hit_walls = deque() #deque for swapping last found walls to first for good guess where to start testing intersections
    wall_start_pos_crosses = deque() #deque has O(1) at it's ends
        
    def point_inside_triangle(self,a,b,c,p):
        """ if point is on the same side of each edge, point is inside triangle"""
        if cross_product(a, b, p) < 0: return False
        if cross_product(b, c, p) < 0: return False
        if cross_product(c, a, p) < 0: return False
        return True
    
    def intersect_edges(self,a,b,c,d,e):
        """intersect two of the edges of fov triangle"""
        if line_line_intersection(a,b,d,e): return True
        if line_line_intersection(c,a,d,e): return True
    
    def line_triangle_intersection(self,a,b,c,d,e):
        """given triangle ABC check if line from D to E intersects"""
        if self.intersect_edges(a,b,c,d,e): return True
        if self.point_inside_triangle(a,b,c,d): return True
        if self.point_inside_triangle(a,b,c,e): return True
        
    def find_collided_walls(self,a,b,c):
        """find walls that are within sight of our fov"""
        Map.hit_walls.clear()
        Map.wall_start_pos_crosses.clear()
        
        for i in Map.all_objects:                  
            if self.line_triangle_intersection(a,b,c,i[1],i[2]):
                Map.hit_walls.append(i)
                Map.wall_start_pos_crosses.append(cross_product(i[1], i[2], a)) #pre calculate crossproduct for wall testing.

class Ray:
    
    def __init__(self, Vect):
        self.ray = Vect
        self.last_found = None
        
    def cast_ray(self,pos):
        self.wall_len = 450.0
        self.end_pos = pos
        multipler = None

        self.color = None

        for idx, wall in enumerate(Map.hit_walls):
            self.sign1 = Map.wall_start_pos_crosses[idx] #precalculated when we tested walls for checking.
            if self.lines_intersect(wall):
                x, y, multipler  = self.distance_to_wall()
                self.end_pos = (x, y) #override endpos to shorter one, so we test less walls.
                self.last_found = idx
                self.color = wall[0]
        
        if self.last_found: #rotate last found wall to first index so we start testing next ray from it
            Map.wall_start_pos_crosses.rotate(-self.last_found)
            Map.hit_walls.rotate(-self.last_found)
        
        if self.color != None:
            return self.color, self.end_pos, multipler

    def lines_intersect(self,wall):
        #calculate area of triangles, crossproduct gives area of square, but we are only
        #interested in sign of it, so no need of dividing it.
        
        #sign1 was precalculated when trying to find walls for testing
        sign2 = cross_product(wall[1], wall[2], self.end_pos)
        if self.sign1 * sign2 < 0: #signs are different if lines intersect
            sign3 = cross_product(wall[1], self.end_pos, self.ray.start_pos)
            # sign1 + sign2 = sign3 + sing4: thus
            sign4 = sign3 + sign2 - self.sign1
            if sign4 * sign3 <= 0:
                self.ratio = self.sign1 / (self.sign1 - sign2) #gives ratio of how far the hit was. 0 < ratio < 1
                return True
            
    def distance_to_wall(self):
        # find intersection on line y = ax + b
        #looks like multiplication is faster than extra lookup thus
        #a + b(c-a) == (1-b)a + b*d
        #where a and c are lookups
        self.wall_len *= self.ratio # wall length must be multiplied with ratio each time wall is found due to replacing testing point to closer one each time.
        return (1-self.ratio) * self.ray.start_pos[0] + self.ratio * self.end_pos[0], (1-self.ratio) * self.ray.start_pos[1] + self.ratio * self.end_pos[1], self.wall_len
        
class Game:
     
    def __init__(self):
        self.map = Map()
        self.screen = pygame.display.set_mode((500,500))
        self.res_x, self.res_y = self.screen.get_size()
        self.res_y *= 0.6 #wall middle point
        self.running = True
        self.angle = 0.0
        self.pos = [250,250]
        self.end_pos = [self.pos[0]-LINE_OF_SIGHT_RADIUS, self.pos[1]]
        self.line_of_sight = Vector(self.pos, self.end_pos)
        self.debug = False
        self.keydown = False
        self.collision = False
        self.ray = Ray(self.line_of_sight)
        self.fov_rays = tuple(range(int(RAYS)))
        self.angle_list = [math.tan(x / LINE_OF_SIGHT_RADIUS) for x in range(-int(RAYS / 2.0), int(RAYS / 2.0))] #one ray to each pixel in plane. 
        self.pre_calc_cosines = tuple([math.cos(x) for x in self.angle_list])
        self.precalc_wall_constants =  list(map(lambda x: WALL_HEIGHT / x, self.pre_calc_cosines))
        #self.pre_calc_fov_rays_angle = list(map(self.angle_ray_ratio.__mul__, range(-250,250)))
        self.pre_calc_fov_rays_angle = self.angle_list
        pygame.mouse.set_visible(False)
       
    def initialize_constants(self):
        """init fov triangle, within this we try to find walls we have to test"""
        self.fov_leftmost = Vector(self.pos, (-200,700)) #calculated end points
        self.fov_rightmost = Vector(self.pos, (-200,-200))
        
    def logic(self):
        #rotate fov_triangle and test walls
        self.fov_leftmost.vect_rotate(self.angle)
        self.fov_rightmost.vect_rotate(self.angle)
        self.map.find_collided_walls(self.pos, (self.fov_leftmost.rot_x_comp, self.fov_leftmost.rot_y_comp), (self.fov_rightmost.rot_x_comp, self.fov_rightmost.rot_y_comp))
        
        #use map to calculate endpoints of rays
        self.end_points = list(map(self.angle.__add__, self.pre_calc_fov_rays_angle))
        self.end_points = list(map(self.end_points_for_angles, self.end_points))
        
    def event_handling(self):
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
               
                if pygame.mouse.get_focused():
                    if event.type == pygame.MOUSEMOTION:        
                        self.angle -= (250 - pygame.mouse.get_pos()[0])/180.0 #calculate offset from mouse and use it as sensitivity
                        pygame.mouse.set_pos((250,250))
                       
                if event.type == pygame.KEYDOWN and event.key == pygame.K_n:
                    self.debug = not self.debug
                                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_w:
                        self.keydown = True
 
                    elif event.key == pygame.K_s:
                        self.line_of_sight.los_vect_rotate(self.angle)
                        self.line_of_sight.unit_vect()
                        self.pos[0] -= self.line_of_sight.unit_x * 10
                        self.pos[1] -= self.line_of_sight.unit_y * 10
                        
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_w:
                        self.keydown = False
						
            if self.keydown and not self.collision:
                self.line_of_sight.los_vect_rotate(self.angle)
                self.line_of_sight.unit_vect()
                self.pos[0] += self.line_of_sight.unit_x * 5 * clock.get_time() / 20
                self.pos[1] += self.line_of_sight.unit_y * 5 * clock.get_time() / 20
    
    def end_points_for_angles(self, angle):
        #line of sight doesn't have y component, so we can have stripperd down version of rotation matrix
        return (math.cos(angle)*-LINE_OF_SIGHT_RADIUS + self.pos[0], math.sin(angle)*-LINE_OF_SIGHT_RADIUS + self.pos[1])
    
    def correct_color(self,list_of_found_hits):
        if list_of_found_hits and list_of_found_hits[2]:
            #could use list comprehencion but it's so slow for high demand calculating
            #for each color component, substract multipler, for shading
            return max(list_of_found_hits[0][0]-list_of_found_hits[2],0), max(list_of_found_hits[0][1]-list_of_found_hits[2],0), max(list_of_found_hits[0][2]-list_of_found_hits[2],0)
    
    def draw(self):
        #environment
                        #canvas        #color      #(start_x, start_y, width, height)
        pygame.draw.rect(self.screen, (30,30,40) ,(0, 0, self.res_x, self.res_y))
        pygame.draw.rect(self.screen, (80,80,80) ,(0, self.res_y, self.res_x, self.res_x))
        
        hits_found = list(map(self.ray.cast_ray, self.end_points)) #calculate hits of each ray.
        colors = list(map(self.correct_color,hits_found)) #correct shading of walls
        
        self.collision = False
        
        #draw walls as seen from "camera"
        for i in self.fov_rays:
            if hits_found[i] != None:
                if hits_found[i][2]:
                    pygame.draw.line(self.screen, colors[i], (i,self.res_y + self.precalc_wall_constants[i] / hits_found[i][2]), (i, self.res_y - self.precalc_wall_constants[i] / hits_found[i][2]))
                    if hits_found[i][2] < 5:
                        self.collision = True
                    
        #draw plain walls
        if self.debug:
            pygame.draw.line(self.screen, (200,200,200), self.pos, (self.fov_leftmost.rot_x_comp, self.fov_leftmost.rot_y_comp))
            pygame.draw.line(self.screen, (200,200,200), self.pos, (self.fov_rightmost.rot_x_comp, self.fov_rightmost.rot_y_comp))
            for i in Map.hit_walls:
                pygame.draw.line(self.screen, *i)
            for i in self.end_points:
                pygame.draw.line(self.screen, (255,255,255), self.pos, i)
                

        pygame.display.flip()
    
    #@profile    
    def run(self):
        self.initialize_constants()
        #for i in range(3000):
        #    self.angle += 1.0 / 500
        while self.running:
            self.event_handling()
            self.logic()
            self.draw()
            clock.tick(1000) #fps limit
            pygame.display.set_caption("fps " + str(clock.get_fps()) + " rays " + str(RAYS))
                    
        pygame.quit()
     
Game().run()

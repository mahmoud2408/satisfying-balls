import math
import sys
import random
import pygame
import pymunk
from pymunk import Segment

WIDTH, HEIGHT = 800, 600
FPS = 60
ARC_THICKNESS = 8
ARC_SEGMENTS = 60
HOLE_ANGLE = math.radians(30)
BASE_RADIUS = 100
RADIUS_STEP = 30
TRAIL_LENGTH = 20

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
space = pymunk.Space()
space.gravity = (0, 900)

cx, cy = WIDTH // 2, HEIGHT // 2
next_radius = BASE_RADIUS
next_ctype = 10
arcs = []
balls = []

class BallTrail:
    def __init__(self, body, shape, color):
        self.body = body
        self.shape = shape
        self.color = color
        self.positions = []

    def update(self):
        self.positions.append(self.body.position)
        if len(self.positions) > TRAIL_LENGTH:
            self.positions.pop(0)

    def draw(self, surf):
        for i, pos in enumerate(self.positions):
            alpha = int(255 * (i + 1) / len(self.positions))
            s = pygame.Surface((self.shape.radius * 2, self.shape.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (self.shape.radius, self.shape.radius), self.shape.radius)
            surf.blit(s, (pos.x - self.shape.radius, pos.y - self.shape.radius))
        x, y = self.body.position
        pygame.draw.circle(surf, (0, 0, 0), (int(x), int(y)), int(self.shape.radius + 2))
        pygame.draw.circle(surf, self.color, (int(x), int(y)), int(self.shape.radius))

def compute_arc_points(r, t0, t1, n):
    return [(r * math.cos(t0 + (t1 - t0) * i / n), r * math.sin(t0 + (t1 - t0) * i / n))
            for i in range(n + 1)]

def spawn_arc(radius, ctype):
    global next_radius, next_ctype
    ang_vel = random.uniform(0.4, 1.0)
    body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    body.position = cx, cy
    body.angular_velocity = ang_vel
    space.add(body)
    hole_c = 3 * math.pi / 2
    start = hole_c + HOLE_ANGLE / 2
    end = hole_c - HOLE_ANGLE / 2 + 2 * math.pi
    pts = compute_arc_points(radius, start, end, ARC_SEGMENTS)
    segs = []
    for a, b in zip(pts, pts[1:]):
        seg = Segment(body, a, b, ARC_THICKNESS)
        seg.elasticity = 1.0
        seg.friction = 0.5
        seg.collision_type = ctype + 1000
        space.add(seg)
        segs.append(seg)
    sensor = Segment(body, pts[-1], pts[0], ARC_THICKNESS)
    sensor.sensor = True
    sensor.collision_type = ctype
    space.add(sensor)
    arc = {'body': body, 'segments': segs, 'sensor': sensor, 'ctype': ctype, 'radius': radius, 'active': True}
    def on_begin(arb, space_ref, _):
        if arc['active']:
            arc['active'] = False
            space_ref.add_post_step_callback(remove_arc, id(arc), arc)
        return False
    handler = space.add_collision_handler(0, ctype)
    handler.begin = on_begin
    arcs.append(arc)
    next_radius += RADIUS_STEP
    next_ctype += 1
    return arc

def remove_arc(space_ref, key, arc):
    if arc['body'] in space_ref.bodies:
        space_ref.remove(arc['body'])
    for s in arc['segments'] + [arc['sensor']]:
        if s in space_ref.shapes:
            space_ref.remove(s)
    if arc in arcs:
        arcs.remove(arc)
    spawn_arc(next_radius, next_ctype)

for _ in range(15):
    spawn_arc(next_radius, next_ctype)

for dx, color in [(-50, (255, 0, 0)), (50, (0, 0, 255))]:
    b = pymunk.Body(1, pymunk.moment_for_circle(1, 0, 10))
    b.position = cx + dx, HEIGHT/2
    b.position = cx + dx, HEIGHT/2
    shape = pymunk.Circle(b, 10)
    shape.elasticity = 0.99
    shape.friction = 0.01
    shape.collision_type = 0
    space.add(b, shape)
    balls.append(BallTrail(b, shape, color))

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    space.step(1 / FPS)
    for bt in balls:
        bt.update()

    screen.fill((0, 0, 0))

    for arc in arcs:
        bdy = arc['body']
        for seg in arc['segments']:
            a = bdy.local_to_world(seg.a)
            c = bdy.local_to_world(seg.b)
            pygame.draw.line(screen, (255, 255, 255), a, c, ARC_THICKNESS)

    for bt in balls:
        bt.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()

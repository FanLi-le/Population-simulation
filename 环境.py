from 基因与状态 import Predator, Prey,Plant,Rock  # 导入子类
import numpy as np
import random
import pygame

class Environment:
    def __init__(self, width=800, height=600):
        self.width = width
        self.height = height
        self.predators = []
        self.prey = []
        self.plants = []  # 新增植物列表
        self.obstacles = []
        self.stats = {"predators": [], "prey": [],"plants":[]}  # 记录每代数量
    
    def add_individuals(self, n_predators=20, n_prey=50,n_plants=0,n_obstacles=10):
        """初始化个体"""
        self.predators = [Predator(random.uniform(0, self.width), random.uniform(0, self.height)) 
                          for _ in range(n_predators)]
        self.prey = [Prey(random.uniform(0, self.width), random.uniform(0, self.height)) 
                     for _ in range(n_prey)]
        self.plants = [Plant(random.uniform(10, self.width - 10), random.uniform(10, self.height- 10)) 
                           for _ in range(n_plants)]  # 初始化植物
        self.obstacles = [Rock(
                x=random.uniform(20, self.width-20),
                y=random.uniform(20, self.height-20),
                radius=random.randint(10, 50)
            )
            for _ in range(n_obstacles)
        ]
    
   
    
    def is_alive(self, individual):
        """扩展存活检查：覆盖植物"""
        alive = (
            individual.energy > 0
            and 0 <= individual.x <= self.width
            and 0 <= individual.y <= self.height
        )
        if not alive:
            # 根据类型移除死亡个体
            if isinstance(individual, Predator):
                self.predators.remove(individual)
            elif isinstance(individual, Prey):
                self.prey.remove(individual)
            elif isinstance(individual, Plant):
                self.plants.remove(individual)
        return alive
    
    def remove_individual(self, individual):
        """移除死亡个体"""
        if individual in self.predators:
            self.predators.remove(individual)
        elif individual in self.prey:
            self.prey.remove(individual)
    
    def update(self):
        """更新所有个体状态"""
        for plant in self.plants[:]:  # 遍历副本避免修改原列表
            if self.is_alive(plant):
                # 植物更新：返回None或新个体（繁殖的后代）
                new_plant = plant.update(self)
                if new_plant:
                    self.plants.append(new_plant)
            else:
                self.plants.remove(plant)
        # 更新捕食者
        for predator in self.predators[:]:
            if self.is_alive(predator):
                predator.move(self)
                predator.check_hunt(self)
                predator.update()
                if predator.can_reproduce():
                    self.predators.append(predator.reproduce())
        
        # 更新被捕食者
        for prey in self.prey[:]:
            if self.is_alive(prey):
                prey.move(self)
                prey.eat_plants(self)
                prey.update()
                if prey.can_reproduce():
                    self.prey.append(prey.reproduce())
        
        # 记录当前种群数量
        self.stats["predators"].append(len(self.predators))
        self.stats["prey"].append(len(self.prey))
        self.stats["plants"].append(len(self.plants))
    
    def draw(self, screen):
        """绘制所有个体"""
        screen.fill((0, 0, 0))  # 黑色背景
        # 绘制捕食者（红色）
        for predator in self.predators:
            pygame.draw.circle(screen, (255, 0, 0), (int(predator.x), int(predator.y)), 4)
        # 绘制被捕食者（蓝色）
        for prey in self.prey:
            pygame.draw.circle(screen, (0, 0,255), (int(prey.x), int(prey.y)), 4)
        for rock in self.obstacles:
            pygame.draw.circle(screen, (150, 150, 150), (int(rock.x), int(rock.y)), rock.radius)
            pygame.draw.circle(screen, (100, 100, 100), (int(rock.x)+3, int(rock.y)-2), rock.radius//3)
            pygame.draw.circle(screen, rock.color, (int(rock.x)-2, int(rock.y)+2), rock.radius//2)
        for plant in self.plants:
            pygame.draw.rect(screen, (0, 255, 0), (int(plant.x), int(plant.y), 2, 5))
            
    
    def check_collision_with_obstacle(self, x, y, radius):
        """检查个体当前位置是否与障碍物碰撞"""
        for obs in self.obstacles:
            if obs.collides_with(x, y, radius):
                return True
        return False
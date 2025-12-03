import numpy as np
import random

# 基因参数示例（可扩展）
GENE_PARAMS = [
    "max_speed",       # 最大速度（影响移动能力）
    "perception",      # 感知范围（能检测到其他个体的距离）
    "aggression",      # 攻击性（捕食者追捕强度，被捕食者逃跑强度）
    "reproduction_rate"# 繁殖所需能量阈值的比例
]

class Individual:
    def __init__(self, x, y, genes=None, is_predator=False):
        self.x = x  # 位置x
        self.y = y  # 位置y
        self.energy = 100  # 初始能量
        self.is_predator = is_predator  # 是否是捕食者
        self.age = 0  # 年龄（可选，用于自然死亡）
        self.radius = 5  # 默认碰撞半径（可调整）
        if genes and "radius" in genes:
            self.radius = genes["radius"]
        
        # 基因：若未指定则随机生成，否则继承（带变异）
        if genes is None:
            self.genes = {"max_speed": random.uniform(1.2, 2),  
                    "perception": random.uniform(10.0, 15.0),  
                    "aggression": random.uniform(0.5, 2.0),
                    "reproduction_rate": random.uniform(0.5, 2.0)}
        else:
            self.genes = self.mutate(genes)  # 继承并变异
        
        # 计算实际属性（由基因决定）
        self.max_speed = self.genes["max_speed"] * (1.5 if is_predator else 1.0)  # 捕食者更快
        self.perception = self.genes["perception"] * (1.5 if is_predator else 1.0)  # 捕食者感知更远
        self.aggression = self.genes["aggression"]
        self.vx = random.uniform(-self.max_speed/2, self.max_speed/2)
        self.vy = random.uniform(-self.max_speed/2, self.max_speed/2)
        #self.velocity = np.array([self.vx, self.vy])
    def mutate(self, genes):
        """基因变异：小概率调整参数"""
        mutated = genes.copy()
        for param in mutated:
            if random.random() < 0.05:  # 5%变异概率
                mutated[param] *= random.uniform(0.8, 1.2)  # 参数波动±20%
        return mutated
    
    def move(self, environment):
        """根据环境决策移动（需子类实现）"""
        
        raise NotImplementedError
    
    
    
    def update(self):
        """更新状态（消耗能量、年龄增长）"""
        self.energy -= 0.2  # 基础代谢消耗
        self.age += 1
    
    def can_reproduce(self):
        """是否满足繁殖条件（能量足够）"""
        return self.energy > 200  # 示例阈值
    
    
    
class Predator(Individual):
    def __init__(self, x, y, genes=None):
        super().__init__(x, y, genes, is_predator=True)
        self.radius = 11  # 稍大的碰撞半径
    
    def move(self, environment):
        """决策：向最近的被捕食者移动"""
        self._check_wall_collision(environment)
        self.handle_collision(environment)
        prey_list = [p for p in environment.prey if environment.is_alive(p)]
        if not prey_list:
            # 没有猎物时随机移动
            self._random_move(environment)
            return
        
        # 找到最近的猎物
        target = min(prey_list, key=lambda p: np.hypot(self.x - p.x, self.y - p.y))
       
        dx = target.x - self.x
        dy = target.y - self.y
        dist = np.hypot(dx, dy)
       
        if dist < self.perception:
            # 向猎物移动（速度受攻击性影响）
            # ✅ 1. 控制转向幅度：每帧最多转max_turn弧度（约5.7度，可调整）
            max_turn = 0.1  # 转向灵活度：值越小越“执着”当前方向，值越大越容易转向
            angle_change = random.uniform(-max_turn, max_turn)
            
            # ✅ 2. 将当前速度转换为极坐标（角度+速率）
            current_angle = np.arctan2(self.vy, self.vx)  # 当前运动方向（弧度）
            speed = np.hypot(self.vx, self.vy)   # 当前速率
            
            # ✅ 3. 计算新方向：当前角度 + 小幅度变化
            new_angle = current_angle 
            
            # ✅ 4. 更新速度向量：保持速率，调整方向
            self.vx = np.cos(new_angle) * speed
            self.vy = np.sin(new_angle) * speed
            speed = self.max_speed * self.aggression
            # next_x = self.x + self.vx
            # next_y = self.y + self.vy
            
           

            self.x += (dx / dist) * min(speed, dist)
            self.y += (dy / dist) * min(speed, dist)

            
        else:
            # 随机探索
            self._random_move(environment)
        
    
    def _check_wall_collision(self, environment):
        """处理触墙反弹"""
        radius = self.radius
        # 左右墙壁碰撞
        if self.x - radius < 0 or self.x + radius > environment.width:
            self.vx *= -1  # 反转x方向速度
        # 上下墙壁碰撞
        if self.y - radius < 0 or self.y + radius > environment.height:
            self.vy *= -1  # 反转y方向速度
        
        # 调整位置确保不穿透边界
        self.x = np.clip(self.x, radius, environment.width - radius)
        self.y = np.clip(self.y, radius, environment.height - radius)
    def _handle_obstacle_collision(self, environment, obstacle, next_pos):
        """
        处理与单个障碍物的碰撞反弹
        """
        self.velocity = np.array([self.vx, self.vy]) # 当前速率
        # 计算个体中心与障碍物中心的相对位置
        dx = next_pos[0] - obstacle.x
        dy = next_pos[1] - obstacle.y
        distance = np.hypot(dx, dy)
        
        # # 计算法线方向（从障碍物指向个体）
       
        normal = np.array([-dx, -dy]) / distance
        
        # 计算切线方向（垂直于法线）
        tangent = np.array([-normal[1], normal[0]])
        
        # 分解速度为法线和切线方向的分量
        v_normal = np.dot(self.velocity, normal) * normal
        v_tangent = np.dot(self.velocity, tangent) * tangent
        
        # # 反弹：法线分量反向，切线分量保留（摩擦力可忽略）
        self.vx, self.vy = v_tangent - v_normal
        
        # 调整位置防止穿透
        self.x = next_pos[0] - normal[0] * self.radius * 0.1
        self.y = next_pos[1] - normal[1] * self.radius * 0.1

    def handle_collision(self, environment):
        next_x = self.x + self.vx
        next_y = self.y + self.vy
        
        # 检查是否与障碍物碰撞
        
        collided_obs = None
        for obs in environment.obstacles:
            if obs.collides_with(next_x, next_y, self.radius):
                collided_obs = obs
                break
        
        if collided_obs:
            self._handle_obstacle_collision(environment, collided_obs, (next_x, next_y))
        else:
            self.x += self.vx
            self.y += self.vy
    def _calculate_normal(self, obstacle):
        """计算障碍物表面的法线向量"""
        dx = self.x - obstacle.x
        dy = self.y - obstacle.y
        distance = np.hypot(dx, dy)
        normal_x = dx / distance
        normal_y = dy / distance
        return (normal_x, normal_y)
    def _random_move(self, environment):
        """平滑的随机运动：保持惯性，仅小幅度调整方向"""
        # ✅ 1. 控制转向幅度：每帧最多转max_turn弧度（约5.7度，可调整）
        max_turn = 0.1  # 转向灵活度：值越小越“执着”当前方向，值越大越容易转向
        angle_change = random.uniform(-max_turn, max_turn)
        
        # ✅ 2. 将当前速度转换为极坐标（角度+速率）
        current_angle = np.arctan2(self.vy, self.vx)  # 当前运动方向（弧度）
        speed = np.hypot(self.vx, self.vy)  # 当前速率
        
        # ✅ 3. 计算新方向：当前角度 + 小幅度变化
        new_angle = current_angle + angle_change
        
        # ✅ 4. 更新速度向量：保持速率，调整方向
        self.vx = np.cos(new_angle) * speed
        self.vy = np.sin(new_angle) * speed
        
       
        
       
        self.x += self.vx
        self.y += self.vy

       
        
    
    def check_hunt(self, environment):
        """检查是否捕获猎物"""
        for prey in environment.prey[:]:  # 遍历副本避免修改原列表
            if environment.is_alive(prey):
                dist = np.hypot(self.x - prey.x, self.y - prey.y)
                if dist < 1.0:  # 捕获距离
                    self.energy += 100  # 获得能量
                    environment.remove_individual(prey)
                    return
    def reproduce(self):
        """繁殖后代（返回新个体）"""
        self.energy /= 2  # 繁殖消耗能量
        return Predator(
            x=self.x + random.uniform(-1, 1),  # 后代出生在附近
            y=self.y + random.uniform(-1, 1),
            genes=self.genes
        )


class Prey(Individual):
    def __init__(self, x, y, genes=None):
        super().__init__(x, y, genes, is_predator=False)
        self.eating_range = self.genes.get("eat_range", 15.0)  # 能检测到植物的范围
        self.plant_seek_aggression = self.genes.get("seek_plant", 1.1)  # 寻找植物的积极性
    
    def move(self, environment):
        """决策：逃避最近的捕食者"""
        self._check_wall_collision(environment)
        self.handle_collision(environment)
        predators = [p for p in environment.predators if environment.is_alive(p)]
        plants = [p for p in environment.plants if environment.is_alive(p)]
        if not predators:
            # 没有捕食者时随机移动（或寻找食物，可扩展）
            self._random_move(environment)
            return
        
        # 找到最近的捕食者和食物
        threat = min(predators, key=lambda p: np.hypot(self.x - p.x, self.y - p.y))
        dx = self.x - threat.x
        dy = self.y - threat.y
        dist = np.hypot(dx, dy)
        
        

        if dist < self.perception:
            # 关键修正：检查距离是否过小
            if dist < 1e-6:
                self._random_move(environment)  # 随机移动代替逃跑
            else:
                # 向猎物移动（速度受攻击性影响）
                # ✅ 1. 控制转向幅度：每帧最多转max_turn弧度（约5.7度，可调整）
                max_turn = 0.1  # 转向灵活度：值越小越“执着”当前方向，值越大越容易转向
                angle_change = random.uniform(-max_turn, max_turn)
                
                # ✅ 2. 将当前速度转换为极坐标（角度+速率）
                current_angle = np.arctan2(self.vy, self.vx)  # 当前运动方向（弧度）
                speed = np.hypot(self.vx, self.vy)  # 当前速率
                
                # ✅ 3. 计算新方向：当前角度 + 小幅度变化
                new_angle = current_angle 
                
                # ✅ 4. 更新速度向量：保持速率，调整方向
                self.vx = np.cos(new_angle) * speed
                self.vy = np.sin(new_angle) * speed
               # self._check_wall_collision(environment)
        
                speed = self.max_speed * self.aggression
                # next_x = self.x + self.vx
                # next_y = self.y + self.vy
                #if environment.check_collision_with_obstacle(next_x, next_y, self.radius):
                #self.handle_collision(environment)
                #else:
                self.x += (dx / dist) * min(speed, dist)
                self.y += (dy / dist) * min(speed, dist)
                # self.x = np.clip(self.x, 0, environment.width)
                # self.y = np.clip(self.y, 0, environment.height)
                
        else:
            target_plant = min(plants, key=lambda p: np.hypot(self.x - p.x, self.y - p.y))
            dx = target_plant.x - self.x
            dy = target_plant.y - self.y
            dist = np.hypot(dx, dy)
            if dist < self.eating_range:
                # if dist < 1e-6:
                #     self._random_move(environment)  # 随机移动代替逃跑
                #else:
                # 向猎物移动（速度受攻击性影响）
                # # ✅ 1. 控制转向幅度：每帧最多转max_turn弧度（约5.7度，可调整）
                # max_turn = 0.1  # 转向灵活度：值越小越“执着”当前方向，值越大越容易转向
                # angle_change = random.uniform(-max_turn, max_turn)
                
                # # ✅ 2. 将当前速度转换为极坐标（角度+速率）
                # current_angle = np.arctan2(self.vy, self.vx)  # 当前运动方向（弧度）
                # speed = np.hypot(self.vx, self.vy)  # 当前速率
                
                # # ✅ 3. 计算新方向：当前角度 + 小幅度变化
                # new_angle = current_angle + angle_change
                
                # # ✅ 4. 更新速度向量：保持速率，调整方向
                # self.vx = np.cos(new_angle) * speed
                # self.vy = np.sin(new_angle) * speed
                speed = self.max_speed# * self.aggression
                # next_x = self.x + self.vx
                # next_y = self.y + self.vy
                #if environment.check_collision_with_obstacle(next_x, next_y, self.radius):
                #self.handle_collision(environment)
                #else:
                self.x += (dx / dist) * min(speed, dist)
                self.y += (dy / dist) * min(speed, dist)
                    
            else:
                self._random_move(environment)
            
       
    def _check_wall_collision(self,environment):
        """处理触墙反弹"""
        radius = self.radius
        # 左右墙壁碰撞
        if self.x - radius < 0 or self.x + radius > environment.width:
            self.vx *= -1  # 反转x方向速度
        # 上下墙壁碰撞
        if self.y - radius < 0 or self.y + radius > environment.height:
            self.vy *= -1  # 反转y方向速度
        
        # 调整位置确保不穿透边界
        self.x = np.clip(self.x, radius, environment.width - radius)
        self.y = np.clip(self.y, radius, environment.height - radius)    
    def handle_collision(self, environment):
        next_x = self.x + self.vx
        next_y = self.y + self.vy
        
        # 检查是否与障碍物碰撞
        
        collided_obs = None
        for obs in environment.obstacles:
            if obs.collides_with(next_x, next_y, self.radius):
                collided_obs = obs
                break
        
        if collided_obs:
            self._handle_obstacle_collision(environment, collided_obs, (next_x, next_y))
        else:
            self.x += self.vx
            self.y += self.vy
        
        # 边界反弹（触墙处理）
        
    
    def _handle_obstacle_collision(self, environment, obstacle, next_pos):
        """
        处理与单个障碍物的碰撞反弹
        """
        self.velocity = np.array([self.vx, self.vy]) # 当前速率
        # 计算个体中心与障碍物中心的相对位置
        dx = next_pos[0] - obstacle.x
        dy = next_pos[1] - obstacle.y
        distance = np.hypot(dx, dy)
        
        # # 计算法线方向（从障碍物指向个体）
       
        normal = np.array([-dx, -dy]) / distance
        
        # 计算切线方向（垂直于法线）
        tangent = np.array([-normal[1], normal[0]])
        
        # 分解速度为法线和切线方向的分量
        v_normal = np.dot(self.velocity, normal) * normal
        v_tangent = np.dot(self.velocity, tangent) * tangent
        
        # # 反弹：法线分量反向，切线分量保留（摩擦力可忽略）
        self.vx, self.vy = v_tangent - v_normal
        
        # 调整位置防止穿透
        self.x = next_pos[0] - normal[0] * self.radius * 0.1
        self.y = next_pos[1] - normal[1] * self.radius * 0.1

   
    
    def _random_move(self, environment):
        """平滑的随机运动：保持惯性，仅小幅度调整方向"""
        # ✅ 1. 控制转向幅度：每帧最多转max_turn弧度（约5.7度，可调整）
        max_turn = 0.1  # 转向灵活度：值越小越“执着”当前方向，值越大越容易转向
        angle_change = random.uniform(-max_turn, max_turn)
        
        # ✅ 2. 将当前速度转换为极坐标（角度+速率）
        current_angle = np.arctan2(self.vy, self.vx)  # 当前运动方向（弧度）
        speed = np.hypot(self.vx, self.vy)  # 当前速率
        
        # ✅ 3. 计算新方向：当前角度 + 小幅度变化
        new_angle = current_angle + angle_change
        
        # ✅ 4. 更新速度向量：保持速率，调整方向
        self.vx = np.cos(new_angle) * speed
        self.vy = np.sin(new_angle) * speed
        
        # # ✅ 5. 限制速度大小（避免突变）
        # self._limit_speed()
        
        # ✅ 6. 移动个体
        # if environment.check_collision_with_obstacle(self.x, self.y, self.radius):
        #     angle_change =  random.uniform(-2, 2) * np.pi
        #     current_angle = np.arctan2(self.vy, self.vx)
        #     new_angle = current_angle + angle_change
        #     speed = np.hypot(self.vx, self.vy)
        #     self.vx = np.cos(new_angle) * speed
        #     self.vy = np.sin(new_angle) * speed
        #     self.x += self.vx
        #     self.y += self.vy
           
       
        self.x += self.vx
        self.y += self.vy
        self.x = np.clip(self.x, 0, environment.width)
        self.y = np.clip(self.y, 0, environment.height)

    
    def eat_plants(self, environment):
        """吃植物：获取能量，植物死亡"""
        for plant in environment.plants[:]:
            if environment.is_alive(plant):
                dist = np.hypot(self.x - plant.x, self.y - plant.y)
                if dist < 1.0:  # 吃的距离
                    # 被捕食者获得能量
                    self.energy += 20
                    # 植物被吃，能量耗尽死亡
                    if plant.be_eaten(amount=15):
                        environment.plants.remove(plant)
                    break  # 一次只吃一个植物，避免重复计算
    def reproduce(self):
        """繁殖后代（返回新个体）"""
        self.energy /= 2  # 繁殖消耗能量
        return Prey(
            x=self.x + random.uniform(-1, 1),  # 后代出生在附近
            y=self.y + random.uniform(-1, 1),
            genes=self.genes)

class Plant(Individual):  # 继承自Individual基类
    def __init__(self, x, y, genes=None):
        super().__init__(x, y, genes, is_predator=False)
        # 植物特有属性：能量、最大能量、繁殖阈值
        self.energy = 50  # 初始能量
        self.max_energy = 100  # 能量上限（避免无限增长）
        self.reproduction_threshold = self.genes.get("repro_thresh", 80)  # 繁殖所需能量阈值
    
    def update(self,environment):
        """植物每帧更新：光合作用增加能量，超过阈值则繁殖"""
        # 光合作用：缓慢增加能量（模拟吸收阳光）
        self.energy = min(self.energy + 0.1, self.max_energy)
        self.min_obstacle_distance = 20
        self.border_buffer = 10
        
        # 能量达标时繁殖：分裂为两个个体（父代能量减半，后代继承基因）
        if self.energy >= self.reproduction_threshold:
            self.energy /= 2  # 繁殖消耗父代能量
            for _ in range(100):
                dx = random.uniform(-50, 50)
                dy = random.uniform(-50, 50)
                new_x = self.x + dx
                new_y = self.y + dy
                
                # 边界检查
                if (new_x < self.border_buffer or
                    new_x > environment.width - self.border_buffer or
                    new_y < self.border_buffer or
                    new_y > environment.height - self.border_buffer):
                    continue
                
                # 障碍物检查
                collision = False
                for obs in environment.obstacles:
                    dist = np.hypot(new_x - obs.x, new_y - obs.y)
                    if dist < obs.radius + self.min_obstacle_distance:
                        collision = True
                        break
                if not collision:
                    return Plant(new_x, new_y, genes=self.genes)
        return None
    
    def be_eaten(self, amount=10):
        """被捕食者取食：减少能量，能量耗尽则死亡"""
        self.energy -= amount
        return self.energy <= 0  # 返回是否死亡
    
    # def draw(self, screen):
    #     """绘制植物（棕色小方块）"""
    #     pygame.draw.rect(screen, (139, 69, 19), (int(self.x)-2, int(self.y)-2, 4, 4))
class Rock:
    def __init__(self, x, y, radius=50):
        self.x = x  # 中心x坐标
        self.y = y  # 中心y坐标
        self.radius = radius  # 碰撞半径（决定大小）
        self.color = (120, 120, 120)  # 灰色外观
    
    
    def collides_with(self, x, y, radius):
        """
        检测与个体的碰撞：
        个体视为圆形，参数为个体的(x,y)和碰撞半径
        """
        distance = np.hypot(self.x - x, self.y - y)
        return distance < (self.radius + radius)  # 圆形碰撞检测
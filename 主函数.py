import pygame
from 环境 import Environment

def main():
    pygame.init()
    width, height = 1100, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("捕食者-被捕食者进化模拟")
    clock = pygame.time.Clock()
    
    env = Environment(width, height)
    env.add_individuals(n_predators=10, n_prey=50,n_plants=70)  # 初始数量
    
    running = True
    font = pygame.font.SysFont(None, 36)
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # 更新环境
        env.update()
        
        # 绘制
        env.draw(screen)
        
        # 显示种群数量
        pred_text = font.render(f"predators: {len(env.predators)}", True, (255, 0, 0))
        prey_text = font.render(f"prey: {len(env.prey)}", True, (0, 0, 255))
        plant_text = font.render(f"plants: {len(env.plants)}", True, (0, 255, 0))
        screen.blit(pred_text, (10, 30))
        screen.blit(prey_text, (10, 50))
        screen.blit(plant_text, (10, 70))
        
        pygame.display.flip()
        clock.tick(30)  # 30帧/秒
    
    pygame.quit()

if __name__ == "__main__":
    main()
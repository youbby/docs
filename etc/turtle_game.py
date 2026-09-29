import turtle
import random
import math

screen = turtle.Screen()
screen.title("거북이 랜덤 탐험")
screen.setup(width=800, height=600)

t = turtle.Turtle()
t.shape("turtle")
t.speed(0)

running = True
remaining_distance = 0

# 거북이 크기를 고려한 화면 여백
MARGIN = 20
STEP = 20


def stop_exploring(event=None):
    """키보드를 누르면 탐험을 종료한다."""
    global running
    running = False

    t.penup()
    t.goto(0, 0)
    t.setheading(0)
    t.write(
        "탐험 종료",
        align="center",
        font=("Arial", 20, "bold")
    )


def explore():
    """거북이를 랜덤한 방향과 거리로 계속 이동시킨다."""
    global remaining_distance

    if not running:
        return

    # 이전에 정한 거리만큼 모두 이동했으면
    # 새로운 방향과 거리를 선택한다.
    if remaining_distance <= 0:
        random_angle = random.randint(-180, 180)
        remaining_distance = random.randint(30, 150)

        t.left(random_angle)

    width_limit = screen.window_width() / 2 - MARGIN
    height_limit = screen.window_height() / 2 - MARGIN

    heading_radian = math.radians(t.heading())

    next_x = t.xcor() + STEP * math.cos(heading_radian)
    next_y = t.ycor() + STEP * math.sin(heading_radian)

    current_heading = t.heading()

    # 좌우 벽에 충돌하면 수평 방향을 반대로 변경
    if next_x >= width_limit or next_x <= -width_limit:
        current_heading = 180 - current_heading
        t.setheading(current_heading)

    # 위아래 벽에 충돌하면 수직 방향을 반대로 변경
    if next_y >= height_limit or next_y <= -height_limit:
        current_heading = -current_heading
        t.setheading(current_heading)

    t.forward(STEP)
    remaining_distance -= STEP

    # 0.02초 후 다시 실행
    screen.ontimer(explore, 1)


# 아무 키나 누르면 종료
window = screen.getcanvas().winfo_toplevel()
window.bind("<Key>", stop_exploring)

screen.listen()
explore()

screen.mainloop()
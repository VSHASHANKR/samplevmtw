import turtle
import math

# --- Config ---
godesses = [
    "Shailaputri", "Brahmacharini", "Chandraghanta",
    "Kushmanda", "Skandamata", "Katyayani",
    "Kalaratri", "Mahagauri", "Siddhidatri"
]
colors = [
    "red", "orange", "gold", "green", 
    "blue", "indigo", "violet", "deeppink", "teal"
]

# --- Setup ---
screen = turtle.Screen()
screen.setup(900, 900)
screen.bgcolor("black")
screen.title("Happy Navaratri")

pen = turtle.Turtle()
pen.hideturtle()
pen.speed(10)

# --- Functions ---
def draw_circle(t, x, y, r, color):
    t.penup()
    t.goto(x, y - r)
    t.pendown()
    t.fillcolor(color)
    t.begin_fill()
    t.circle(r)
    t.end_fill()

def write_text(t, x, y, text, color="white", size=12, align="center"):
    t.penup()
    t.goto(x, y)
    t.pendown()
    t.color(color)
    t.write(text, align=align, font=("Arial", size, "bold"))

def draw_goddess_circle():
    radius = 250
    angle_gap = 360 / len(godesses)
    for i, goddess in enumerate(godesses):
        angle = math.radians(i * angle_gap)
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        draw_circle(pen, x, y, 50, colors[i])
        write_text(pen, x, y - 5, goddess, "white", 10)

def draw_center_message():
    write_text(pen, 0, 30, "🌸 Happy Navaratri 🌸", "yellow", 24)
    write_text(pen, 0, -10, "May Maa Durga bless you with power, prosperity & peace", "lightgreen", 14)

# --- Main ---
draw_goddess_circle()
draw_center_message()

turtle.done()

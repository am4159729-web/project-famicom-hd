import pytest

pygame = pytest.importorskip("pygame")
if not hasattr(pygame, "K_UP"):
    pytest.skip("needs the real pygame")

from famicon.app import read_controls  # noqa: E402


def test_arrow_and_wasd_both_move():
    c = read_controls(lambda k: k in (pygame.K_UP, pygame.K_a), set())
    assert c.up and c.left and not c.down and not c.right


def test_press_events_map_to_buttons():
    c = read_controls(lambda k: False, {pygame.K_z, pygame.K_RETURN})
    assert c.a_press and c.start_press and not c.b_press and not c.back_press
    c = read_controls(lambda k: False, {pygame.K_x, pygame.K_ESCAPE})
    assert c.b_press and c.back_press

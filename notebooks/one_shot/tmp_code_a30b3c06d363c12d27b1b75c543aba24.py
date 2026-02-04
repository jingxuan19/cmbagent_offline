import os
import datetime
import matplotlib.pyplot as plt

def expected_remaining(g, b, r, _cache={}):
    """Return the expected number of balls remaining when drawing without replacement
    until one colour is exhausted, starting from g green, b blue and r red balls.
    Uses memoization to avoid recomputation."""
    if g == 0 or b == 0 or r == 0:
        return g + b + r
    key = (g, b, r)
    if key in _cache:
        return _cache[key]
    total = g + b + r
    exp_val = (g / total) * expected_remaining(g - 1, b, r, _cache)
    exp_val += (b / total) * expected_remaining(g, b - 1, r, _cache)
    exp_val += (r / total) * expected_remaining(g, b, r - 1, _cache)
    _cache[key] = exp_val
    return exp_val

def generate_series(fixed_b, fixed_r, g_range):
    """Compute expected remaining values for varying green counts."""
    return [expected_remaining(g, fixed_b, fixed_r) for g in g_range]

def generate_series_fixed_g(fixed_g, fixed_r, b_range):
    """Compute expected remaining values for varying blue counts."""
    return [expected_remaining(fixed_g, b, fixed_r) for b in b_range]

def generate_series_fixed_gb(fixed_g, fixed_b, r_range):
    """Compute expected remaining values for varying red counts."""
    return [expected_remaining(fixed_g, fixed_b, r) for r in r_range]

if __name__ == '__main__':
    # Original numbers
    G0 = 35
    B0 = 25
    R0 = 40

    # Ranges for plotting
    g_vals = list(range(5, 61, 5))
    b_vals = list(range(5, 61, 5))
    r_vals = list(range(5, 61, 5))

    # Compute series
    exp_g = generate_series(B0, R0, g_vals)
    exp_b = generate_series_fixed_g(G0, R0, b_vals)
    exp_r = generate_series_fixed_gb(G0, B0, r_vals)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(g_vals, exp_g, marker='o', label='Varying Green')
    plt.plot(b_vals, exp_b, marker='s', label='Varying Blue')
    plt.plot(r_vals, exp_r, marker='^', label='Varying Red')
    plt.title('Expected Balls Remaining vs. Colour Count')
    plt.xlabel('Number of Balls')
    plt.ylabel('Expected Remaining Balls')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # Ensure data directory exists
    data_dir = 'data'
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = 'expected_remaining_plot_1_' + timestamp + '.png'
    filepath = os.path.join(data_dir, filename)
    plt.savefig(filepath, dpi=300)
    print('Plot saved to ' + filepath)

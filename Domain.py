import numpy as np
import BlackHoleOrbiter as BHO
import KerrSchild as KS

def RebasedStep(particles, ghosts, observer_name, dlambda, R0):
    particles_by_name = {p.name: p for p in particles}
    observer = particles_by_name[observer_name]

    # 1. Capture the observer-centric retarded events while caches are still valid
    view_events = BHO.build_observer_view(observer, particles, ghosts)

    # 2. Clear every cache
    for p in particles:
        p._cache.clear()
    for g in ghosts:
        g._cache.clear()

    # 3. Index the events by name so we assign each particle only its own data
    events_by_name = {ev['name']: ev for ev in view_events}

    # 4. Re-instantiate every non-observer particle from its matching retarded event
    for p in particles:
        if p is observer:
            continue
        ev = events_by_name.get(p.name)
        if ev is None:
            # particle was not visible; drop it.
            continue
        p.pos = np.asarray(R0 @ ev["x4_obs"], dtype=np.float64)
        p.vel = np.asarray(R0 @ ev["v4_obs"], dtype=np.float64)
        p.spin = np.asarray(R0 @ ev["j4_obs"], dtype=np.float64)
        p.mass = float(ev["src_mass"])
        p.proper_time = 0.0
        p.birth_time = p.pos[0]
        p.spin = KS.Initialize_spin_vector(p.spin, p.vel)

    # 5. Place the observer at the origin of its own rest frame (once)
    observer.pos = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    observer.vel = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    observer.spin = KS.Initialize_spin_vector(
        np.zeros(4, dtype=np.float64), observer.vel
    )
    observer.proper_time = 0.0
    observer.birth_time = 0.0

    # 6. Reseed every cache with one valid snapshot
    for p in particles:
        p.record()
    for g in ghosts:
        g.record()

    return particles, observer_name, dlambda
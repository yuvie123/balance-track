from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import fetch, pipeline
from .outline import SYSTEMS
from .simulate import PROFILES, simulate, write_csv


def add_person_args(p):
    p.add_argument("csv", type=Path)
    p.add_argument("--height", type=float, required=True, help="cm")
    p.add_argument("--weight", type=float, required=True, help="kg")
    p.add_argument("--shoe", type=float, required=True)
    p.add_argument("--system", choices=SYSTEMS, default="us-men")
    p.add_argument("--foot", choices=["left", "right"], default="left", help="foot the sensor insole was on")
    p.add_argument("-o", "--out", type=Path, default=Path("out"))
    p.add_argument("--no-plot", action="store_true")


def print_result(result):
    s = result["summary"]
    print(f"{s['strides']} strides, cadence {s['cadence_spm']:.0f} steps/min, stride {s['stride_time_s']:.2f}s")
    print(f"stance roll {s['stance_roll_deg']:+.1f} deg (sd {s['stance_roll_sd_deg']:.1f}), "
          f"heel strike {s['peak_accel_mps2']:.1f} m/s^2")
    if result["rules"]:
        for r in result["rules"]:
            print(f"  + {r['rule']}: {r['mm']:.1f} mm ({r['reason']})")
    else:
        print("  gait looks normal, flat 3 mm insole")
    ins = result["insole"]
    print(f"insole {ins['length_mm']:.0f} mm long, {ins['min_mm']:.1f}-{ins['max_mm']:.1f} mm thick")


def cmd_fetch(args):
    sessions = fetch.list_sessions(args.host)
    if not sessions:
        print("no sessions on the insole")
        return
    names = [s["name"] for s in sessions]
    if args.session:
        names = [n for n in names if n == args.session]
        if not names:
            sys.exit(f"{args.session} not found, have: {', '.join(s['name'] for s in sessions)}")
    elif not args.all:
        names = [sorted(names)[-1]]

    for name in names:
        path = fetch.download(args.host, name, args.out)
        print(f"saved {path}")
        if args.delete:
            fetch.delete(args.host, name)


def cmd_analyze(args):
    result = pipeline.analyze(args.csv, args.out, args.height, args.weight, args.shoe,
                              args.system, args.foot, plot=not args.no_plot)
    print_result(result)


def cmd_build(args):
    npz = args.input
    if npz.is_dir():
        found = sorted(npz.glob("insole_*.npz"))
        if not found:
            sys.exit(f"no insole_*.npz in {npz}, run analyze first")
        npz = found[0]
    stl = args.stl or npz.with_suffix(".stl")
    info = pipeline.build(npz, stl, mirror=args.mirror)
    print(f"wrote {stl} ({info['triangles']} triangles, {info['volume_cm3']:.1f} cm^3)")


def cmd_run(args):
    result = pipeline.analyze(args.csv, args.out, args.height, args.weight, args.shoe,
                              args.system, args.foot, plot=not args.no_plot)
    print_result(result)

    npz = args.out / f"insole_{args.foot}.npz"
    stl = args.out / f"insole_{args.foot}.stl"
    info = pipeline.build(npz, stl)
    print(f"wrote {stl} ({info['triangles']} triangles, {info['volume_cm3']:.1f} cm^3)")

    if args.both:
        other = "right" if args.foot == "left" else "left"
        stl = args.out / f"insole_{other}.stl"
        pipeline.build(npz, stl, mirror=True)
        print(f"wrote {stl} (mirrored)")


def cmd_simulate(args):
    data, strikes = simulate(args.profile, args.minutes, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.out, data)
    print(f"wrote {args.out} ({len(data)} rows, {len(strikes)} strides, {args.profile})")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="balancetrack")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    p = sub.add_parser("fetch", help="download sessions from the insole over wifi")
    p.add_argument("--host", default="192.168.4.1")
    p.add_argument("--session")
    p.add_argument("--all", action="store_true")
    p.add_argument("--delete", action="store_true", help="remove from the insole after downloading")
    p.add_argument("-o", "--out", type=Path, default=Path("data"))
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("analyze", help="gait report and thickness map from a session")
    add_person_args(p)
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("build", help="turn a thickness map into an STL")
    p.add_argument("input", type=Path, help="insole_*.npz or the analyze output folder")
    p.add_argument("-o", "--stl", type=Path)
    p.add_argument("--mirror", action="store_true")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("run", help="analyze and build in one go")
    add_person_args(p)
    p.add_argument("--both", action="store_true", help="also write a mirrored insole for the other foot")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("simulate", help="make a fake session to test with")
    p.add_argument("--profile", choices=list(PROFILES), default="normal")
    p.add_argument("--minutes", type=float, default=2.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("-o", "--out", type=Path, default=Path("examples/sample_session.csv"))
    p.set_defaults(func=cmd_simulate)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (ValueError, OSError) as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()

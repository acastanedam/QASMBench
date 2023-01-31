OPENQASM 2.0;
include "qelib1.inc";

qreg a[3];
creg c[3];

ccx a[0],a[1],a[2];
measure a[0] -> c[0];
measure a[1] -> c[1];
measure a[2] -> c[2];

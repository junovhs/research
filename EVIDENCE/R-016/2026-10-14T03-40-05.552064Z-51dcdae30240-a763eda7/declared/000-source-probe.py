"""R-016: sampled comparison of scalar vs spatial Allen-Cahn bounds; not a proof."""
import json, math, os
from pathlib import Path
c=json.loads(Path('config.json').read_text())
D=c['sites']; T=c['prefix']; A=c['forcing_amplitude']; N=c['steps_per_unit']
assert (D,T,A)==(16,10.5,0.25)
f=lambda x:x-x*x*x
flow=lambda x:1/math.sqrt(1+(x**-2-1)*math.exp(-2*T))
low,high=flow(.5),flow(2.0)
x0=[.5+1.5*((5*i+3)%16)/15 for i in range(D)]

def rk4(y,b,steps,h):
    def rhs(v):return [v[(i-1)%D]-2*v[i]+v[(i+1)%D]+f(v[i])+b[i] for i in range(D)]
    def plus(v,k,z):return [p+z*q for p,q in zip(v,k)]
    for _ in range(steps):
        p=rhs(y); q=rhs(plus(y,p,h/2));r=rhs(plus(y,q,h/2));s=rhs(plus(y,r,h))
        y=[v+h*(a+2*b+2*d+e)/6 for v,a,b,d,e in zip(y,p,q,r,s)]
    return y

def scalar(x,b,n,h):
    for _ in range(n):
        a=f(x)+b;z=f(x+h*a/2)+b;d=f(x+h*z/2)+b;e=f(x+h*d)+b
        x+=h*(a+2*z+2*d+e)/6
    return x

def drive(case):
    if case=='no_pulse':return [0.]*D
    if case=='uniform_minus':return [-A]*D
    if case=='smooth_cosine':return [A*math.cos(2*math.pi*i/D) for i in range(D)]
    if case=='localized_plus':return [A if i==0 else 0. for i in range(D)]
    raise ValueError(case)

out={'initial':x0,'prefix_scalar_bounds':[low,high], 'cases':{}}
for name in c['cases']:
    b=drive(name); sample=[]
    for n in N:
        h=1/n
        y=rk4(rk4(x0,[0.]*D,round(T*n),h),b,n,h)
        a=rk4([low]*D,b,n,h);z=rk4([high]*D,b,n,h)
        l=scalar(low,min(b),n,h);u=scalar(high,max(b),n,h)
        sample.append({'h':h,'center':y[0],'spatial':[a[0],z[0]],'scalar':[l,u],
                       'all_in_spatial':all(a[i]-1e-12<=y[i]<=z[i]+1e-12 for i in range(D))})
    coarse,fine=sample
    out['cases'][name]={'forcing_extrema':[min(b),max(b)],'fine':fine,
       'center_step_change':abs(coarse['center']-fine['center']),
       'spatial_bound_step_change':max(abs(x-y) for x,y in zip(coarse['spatial'],fine['spatial'])),
       'scalar_bound_step_change':max(abs(x-y) for x,y in zip(coarse['scalar'],fine['scalar']))}
# On [0.8,1.2], f' >= -3.32 and scalar +/-0.25 remain inside that box.
# Thus global-scalar width w' >= -3.32*w+0.5 and w(0)>=0.
out['global_scalar_lower_bound']=(.5/3.32)*(1-math.exp(-3.32))
Path(os.environ['DTL_RUN_DIR'],'output.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print('Completed R-016',len(out['cases']),'cases')

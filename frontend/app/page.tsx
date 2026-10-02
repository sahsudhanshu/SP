import {Suspense} from 'react';
import RiskWorkspace from '@/components/RiskWorkspace';
export default function Page(){return <Suspense fallback={<div className="empty">Loading portfolio intelligence…</div>}><RiskWorkspace/></Suspense>}


import {Suspense} from 'react';
import RiskWorkspace from '@/components/RiskWorkspace';
export const dynamicParams=false;
export function generateStaticParams(){return ['risk-feed','risk-map','portfolio','stress-testing','timeline','alerts','heatmap','audit','evaluation'].map(section=>({section}))}
export default function Page(){return <Suspense fallback={<div className="empty">Loading portfolio intelligence…</div>}><RiskWorkspace/></Suspense>}


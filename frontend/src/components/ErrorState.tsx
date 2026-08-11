export default function ErrorState({ message }: { message: string }) { return <div className="state error" role="alert"><strong>Data unavailable</strong><span>{message}</span></div> }

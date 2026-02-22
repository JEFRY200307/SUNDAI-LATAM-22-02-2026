export default function PhoneWrapper({ children }) {
    return (
        <div className="w-[320px] h-[640px] bg-slate-900 rounded-[2.5rem] p-3 shadow-2xl relative border-4 border-slate-800 flex flex-col shrink-0">
            <div className="absolute top-0 inset-x-0 h-6 flex justify-center z-20">
                <div className="w-32 h-6 bg-slate-800 rounded-b-xl"></div>
            </div>
            <div className="flex-1 bg-white rounded-[2rem] overflow-hidden flex flex-col relative pt-6">
                {children}
            </div>
        </div>
    )
}

function dataActual = SpikerStream(totalTime,inputBufferSize,maxTime,portNumber)
% Function reads data from BackyardBrain's Arduino SpikerShield
% https://backyardbrains.com/products/heartAndBrainSpikerShieldBundle

%---INPUTS:
% totalTime: code will stop after this many seconds [1 s = 20000 buffer size]
% inputBufferSize: buffer size (in the range 1000-20000)
%                   e.g., inputBufferSize = 20000 means it waits
%                           1 second before plotting
% maxTime: time plotted in window [s]
% portNumber: the port to read data from.
%        change this to match the number in (e.g., Device Manager on Windows)
%-------------------------------------------------------------------------------
%-------------------------------------------------------------------------------

% CHECK INPUTS/SET DEFAULTS:
if nargin < 1
    totalTime = 5;
end
if nargin < 2
    inputBufferSize = 500;
end
if nargin < 3
    maxTime = 5;
end
if nargin < 4
    portNumber = 6;
end

delete(instrfindall);

%-------------------------------------------------------------------------------
% Initialize import data stream
%-------------------------------------------------------------------------------
s = InitializePortInput(inputBufferSize,portNumber);

%-------------------------------------------------------------------------------
% Record and plot data
%-------------------------------------------------------------------------------
figure('color','w');
ax = gca();
xlabel('Time (s)')
ylabel('Input signal (arb)')

numLoops = 20000/s.InputBufferSize*totalTime;

% Length of time that data is acquired for:
T_acquire = s.InputBufferSize/20000;

% Total number of loops to cover desired time window:
numMaxLoops = maxTime/T_acquire;

for i = 1:numLoops
    % take enough data to cover the first time window

    % read and process data first
    data = fread(s)';
    dataTemp = process_data(data);

    % start loops
    if i <= numMaxLoops
        if i==1
            dataActual = dataTemp;
            
            dataMean = median(dataTemp);
        else
            dataActual = [dataTemp dataActual]; % the result stream will be in data variable
            
            dataMean = [median(dataTemp) dataMean];
        end
    else
        % continue adding data to the time window after window is finished
        dataActual = circshift(dataActual,[0 length(dataTemp)]);
        dataActual(1:length(dataTemp)) = dataTemp';
        
        dataMean = circshift(dataMean,[0 1]);
    end

    t = min(i,numMaxLoops)*s.InputBufferSize/20000*linspace(0,1,length(dataActual));
    
    %addition here pog
    t2 = min(i,numMaxLoops)*s.InputBufferSize/20000*linspace(0,1,length(dataMean));
    
    disp(mean(dataTemp));
    
    plot(t,dataActual);
    hold on
    plot(t2,dataMean);
    hold off
    ax.XLim = [0,maxTime];
    drawnow;
end

end
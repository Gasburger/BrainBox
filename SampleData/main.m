function main(currentWeek, displayPlots)
    % Default to not showing plots
    if nargin < 2
        displayPlots = false;
    end

    % Show plots
    if displayPlots
        set(groot, "defaultFigureVisible", "on");
    % Don't show plots
    else
        set(groot, "defaultFigureVisible", "off");
    end


    % Get list of wav files in the current week directory
    files = dir(sprintf("Week %d/*.wav", currentWeek));

    for i = 1:length(files)
        filename = files(i).name;
        % Send output to the /Week {currentWeek}/Output/ directory
        newFilename = append(sprintf("Week %d/Output/", currentWeek), strrep(filename, ".wav", ""));
        % Read the current wav file
        [data, Fs] = audioread(append(sprintf("Week %d/", currentWeek), filename));
        
        % Corresponding time in seconds
        t = linspace(0, size(data, 1)/Fs, size(data, 1));

        % Annotations: tag -> time
        annotationFilename = append(sprintf("Week %d/", currentWeek), strrep(filename, ".wav", ".txt"));
        annotations = parser(annotationFilename);

        % Ignore the waveform before the flag
        if annotations.isKey("ignore")
            minimumTime = annotations("ignore") + 0.001*abs(t(end) - t(1));
        else
            minimumTime = 0;
        end

        % Plot the waveform
        figure();
        dataPlot = plot(linspace(0, size(data, 1)/Fs, size(data, 1)), data, "Color", "black");
        suppressLegend(dataPlot);
        xlim([minimumTime, size(data, 1)/Fs]);
        % Save unannotated plot
        f = gcf;
        saveas(f, append(newFilename, "_waveform.png"));
        % Add annotations if events.txt exist
        if ~isempty(annotations)
            addAnnotations(annotations);
            % Save annotated plot
            f = gcf;
            saveas(f, append(newFilename, "_waveform_annotated.png"));
        end

        % Downsample data to make processing faster
        downsampledData = downsample(data, 20);

        % Plot spectrogram of data
        figure();
        spectrogram(downsampledData, 256, 250, 256, 500, "yaxis");
        if t(end) > 60
            xlim([minimumTime / 60, inf]);
        else
            xlim([minimumTime, inf]);
        end
        ylim([0, 90]);
        colormap(winter);
        brighten(-0.7);
        % Save unannotated plot
        f = gcf;
        % saveas(f, append(newFilename, "_spectrogram.png"));
        % Add annotations if events.txt exist
        if ~isempty(annotations)
            addAnnotations(annotations, t(end) > 60);
            % Save annotated plot
            f = gcf;
            % saveas(f, append(newFilename, "_spectrogram_annotated.png"));
        end

        % Get the spectrogram data
        [d, freq, t] = spectrogram(downsampledData, 256, 250, 256, 500, "yaxis");
        
        % Take the real part of the Fourier transform
        dReal = real(d);
        
        % Take the mean of the power over frequencies around 10 Hz
        AlphaRange = mean(dReal((5:7), :), 1);

        % Take a moving average of the power
        SmoothedAlphaRange = smooth((abs(AlphaRange)), 250, "moving");
        % SmoothedAlphaRange = 10.^abs(AlphaRange);
        
        % Plot power of the alpha wave frequencies over time
        figure();
        dataPlot = plot(t/60, SmoothedAlphaRange, "Color", "black");
        suppressLegend(dataPlot);
        xlabel("Time (minutes)");
        xlim([minimumTime/60, max(t/60)]);
        % Save unannotated plot
        f = gcf;
        % saveas(f, append(newFilename, "_smoothedalpharange.png"));
        % Add annotations if events.txt exist
        if ~isempty(annotations)
            addAnnotations(annotations, true);
            % Save unannotated plot
            f = gcf;
            % saveas(f, append(newFilename, "_smoothedalpharange_annotated.png"));
        end
    end
end


function suppressLegend(fig)
    % Suppress icon display so that it is not shown in the legend
    set(get(get(fig, "Annotation"), "LegendInformation"), "IconDisplayStyle", "off");
end


function rgbMatrix = distinctColors(numColors)
    % Get `numColors` distinct colors by evenly spacing out hue.
    hsvMatrix = zeros(numColors, 3);
    for colorIndex = 1:numColors
        hue = colorIndex * mod(360 / numColors, 360);
        hsvMatrix(colorIndex, :) = [hue / 360, 1, 1];
    end
    rgbMatrix = hsv2rgb(hsvMatrix);
end


function addAnnotations(annotations, toMinutes)
    % Add vertical lines as given by the annotations tags.
    if nargin < 2
        toMinutes = false;
    end

    numColors = length(annotations);
    % Ignore flag is not to be plotted
    if annotations.isKey("ignore")
        numColors = numColors - 1;
    end
    % `numColors` distinct colors
    annotationColors = distinctColors(numColors);

    % Legend data
    legendEntries = cell(numColors, 1);

    % Add annotations
    colorIndex = 1;
    for annotationKey = annotations.keys
        % Don't plot ignore tags
        if strcmp(char(annotationKey), "ignore")
            continue;
        end

        % Current plot color
        currentColor = annotationColors(colorIndex, :);
        % Current tag
        legendEntries{colorIndex} = char(annotationKey);

        first = true;
        for timestampValue = annotations(char(annotationKey))
            % Convert to minutes if necessary
            if toMinutes
                xValue = timestampValue / 60;
            % Leave as seconds
            else
                xValue = timestampValue;
            end

            % Plot vertical line
            xl = xline(xValue, "--", "Color", currentColor, "LineWidth", 1.25);

            if first
                first = false;
            % Suppress legend output
            else
                suppressLegend(xl);
            end
        end
        colorIndex = colorIndex + 1;
    end
    % Add legend
    legend(legendEntries);
end

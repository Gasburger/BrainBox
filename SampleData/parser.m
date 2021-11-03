
function annotations = parser(inputFile)
    % Parse events.txt files

    % Initialise map
    annotations = containers.Map("keyType", "char", "valueType", "any");

    % Check if the file exists
    if ~isfile(inputFile)
        fprintf("%s does not exist!\n", inputFile);
        return;
    end

    % Read file
    textFile = fileread(inputFile);
    lines = splitlines(textFile);

    for i = 1:length(lines)
        currentLine = lines(i);
        % Ignore lines tagged with # and empty lines
        if ~contains(currentLine, "#") && currentLine ~= ""
            result = split(currentLine, sprintf(",\t"));
            % Tag name
            currentKey = char(result(1));
            % Timestamp
            currentValue = str2double(result(2));
            % Append timestamp
            if annotations.isKey(result(1))
                annotations(currentKey) = [annotations(currentKey), currentValue];
            else
                annotations(currentKey) = currentValue;
            end
        end
    end
end

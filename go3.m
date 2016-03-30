function [x,sx] = go3()
% Problem: Find the first point whose the total score is positive

% get instance ===============================================
[p,s] = instance_random();

% identifies which variables are considered by each pattern
mask = logical(p);

% search =====================================================
[~,n]  = size(p);
x      = ones(1,n); % starting point
[x,sx] = search_brute(x,mask,p,s);

if(sx > 0)
    fprintf('\nA solution has been found.\n');
    fprintf('x = '); fprintf('% d ', x); fprintf('\n');
    fprintf('s = % d\n', sx);
    [sx,sp] = score(x,mask,p,s);
    fprintf('> Checking \n');
    for i = 1:length(sp)
        fprintf('% d ', p(i,:));
        fprintf(' | % d [% d]\n', s(i), sp(i));
    end
    fprintf('\n');
else
    fprintf('\nNo solution has been found.\n');
end
end

function [p,s] = instance_random()
m    = 10;  % number of patterns
n    = 5;   % problem dimension
dvar = 0.1; % density of variables used in each pattern
bvar = 0.5; % patterns
bsgn = 0.5; % patterns signal bias

% p(i) = {0, then x(i) is ignored; +1 or -1, then x(i) == p(i)}
p = (rand(m,n) > (1-dvar)) .* (-1).^(rand(m,n) > bvar); % logical vector

% removing empty patterns
irow = logical(logical(p) * ones(n,1));
p    = p(irow,:);

% removing ignored variables
[m,~] = size(p);
icol  = logical(ones(1,m) * logical(p));
p     = p(:,icol);

% actual problem size
[m,~] = size(p);

% s(i) = {+1|-1} score
s = ones(m,1) .* (-1).^(rand(m,1) > bsgn); % signals {-1 | +1}

fprintf('> Instance\n');
for i = 1:m
    fprintf('% d ', p(i,:));
    fprintf(' | % d\n', s(i));
end
fprintf('\n');
end

function [sx,sp] = score(x,mask,p,s)
[m,~] = size(p);
sp     = zeros(m, 1);
for j = 1:m
    pj    = p(j,mask(j,:));
    xj    = x(mask(j,:));
    sp(j) = all(pj == xj) * s(j);
end
sx = sum(sp);
end

function [x,sx] = search_brute(x,mask,p,s)
n  = length(x);

fprintf('> Searching\n');

tic
sx = score(x,mask,p,s);

fprintf('Level %3d/%d    completed after %3.2f seconds\n',0,n,toc);
if(sx > 0)
    return;
end

for dist = 1:n
    hasnext = true;
    iset    = 1:dist;
    tic
    while((sx < 1) && hasnext)
        % move to next
        x(iset) = x(iset) * (-1); % flip
        
        % a solution has been found
        sx = score(x,mask,p,s);
        if(sx > 0)
            fprintf('Level %3d/%d    completed after %3.2f seconds\n',dist,n,toc);
            return;
        end
        
        % restore original solution
        x(iset) = x(iset) * (-1); % flip
        
        % next subset of indices
        j = dist; % last index
        while(j > 0)
            % max value of iset(j) is n-(dist-j)
            if(iset(j) < (n-(dist-j)))
                hasnext = true;
                iset(j) = iset(j) + 1;
                for k = (j+1):dist
                    iset(k) = iset(k-1) + 1;
                end
                break;
            else
                j = j - 1;
            end
            hasnext = false;
        end
    end
    fprintf('Level %3d/%d    completed after %3.2f seconds\n',dist,n,toc);
end
end